from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.apps import apps
from django.db.models import Prefetch
from django.core.exceptions import FieldError
import re

from .exceptions import QueryLangException
from .settings import api_settings

class QueryLangParser:
    """
    Classe de parsing pour des query strings comme:
    Agent{"nom", "prenom", Contrat:contrats[{"date_debut"}
    User{"email", Profile:profile{"bio", "avatar"}, Post:articles[{"title", "date_creation"}]}
    1. Parse la string pour extraire le modèle, les champs, et les relations
    2. Génère un queryset optimisé avec select_related et prefetch_related
    """
    def __init__(self, query_string):
        """Initialise avec la query string à parser"""
        self.query_string = query_string
        self.parsed_data = self._parse()
        
    def _parse(self):
        """
        Parse une query string comme: Agent{"nom", "prenom", Contrat:contrats[{"date_debut"}]}
        Retourne: {
            'model': 'Agent',
            'fields': ['nom', 'prenom'],
            'relations': {
                'contrats': {
                    'model': 'Contrat',
                    'fields': ['date_debut'],
                    'is_many': True
                }
            }
        }
        """
        # Regex pour matcher le pattern principal: ModelName{...}
        main_pattern = r'(\w+)\{(.*)\}'
        match = re.match(main_pattern, self.query_string.strip())
        
        if not match:
            raise ValueError("Query must start with ModelName{...}")
        
        model_name = match.group(1)
        if model_name in api_settings.UNAUTHORIZED_MODELS: raise QueryLangException(f'Unauthorized model: {model_name}', 'forbidden_query_model')
        content = match.group(2)
        
        result = {
            'model': model_name,
            'fields': [],
            'relations': {}
        }
        
        # Parser le contenu entre {}
        self._parse_fields_content(content, result)
        
        return result
    
    def _parse_fields_content(self, content, result):
        """Parse le contenu entre {} pour extraire fields et relations"""
        # Tokenizer simple pour gérer les imbrications
        tokens = []
        current_token = ""
        depth = 0
        in_quotes = False
        
        i = 0
        while i < len(content):
            char = content[i]
            
            if char == '"' and (i == 0 or content[i-1] != '\\'):
                in_quotes = not in_quotes
                current_token += char
            elif in_quotes:
                current_token += char
            elif char in '{[':
                depth += 1
                current_token += char
            elif char in '}]':
                depth -= 1
                current_token += char
            elif char == ',' and depth == 0:
                # Fin d'un token au niveau racine
                if current_token.strip():
                    tokens.append(current_token.strip())
                current_token = ""
            else:
                current_token += char
            
            i += 1
        
        # Ajouter le dernier token
        if current_token.strip():
            tokens.append(current_token.strip())
        
        # Analyser chaque token
        for token in tokens:
            token = token.strip().strip('"')  # Enlever les quotes
            
            if token.split(':')[0] in api_settings.UNAUTHORIZED_KEYS: raise QueryLangException(f"Unauthorized key: {token.split(':')[0]}", 'forbidden_query_key')
            
            if ':' in token:
                # Relation: Contrat:contrats[{"date_debut"}] ou Profile:profile{"bio"}
                self._parse_relation_token(token, result)
            else:
                # Champ simple: "nom", "prenom"
                if token:
                    result['fields'].append(token)
                    
    def _parse_relation_token(self, token, result):
        """Parse un token de relation comme Contrat:contrats[{"date_debut"}] ou Contrat:contrats:max(date_debut)[{"date_debut"}]"""
        # Séparer model:key et le reste
        colon_pos = token.find(':')
        model_name = token[:colon_pos]
        if model_name in api_settings.UNAUTHORIZED_MODELS: raise QueryLangException(f'Unauthorized model: {model_name}', 'forbidden_query_model')
        rest = token[colon_pos + 1:]
        
        # Détecter les fonctions: contrats:max(date_debut)[{...}]
        func_pattern = r'(\w+):(\w+)\(([^)]*)\)\[(.+)\]'
        func_match = re.match(func_pattern, rest)
        
        function_info = None
        
        if func_match:
            # Fonction détectée
            key_name = func_match.group(1)
            func_name = func_match.group(2)
            func_field = func_match.group(3) if func_match.group(3) else None
            nested_content = func_match.group(4)
            is_many = False
            
            function_info = {
                'name': func_name,
                'field': func_field
            }
        else:
            # Identifier si c'est une relation many ou single
            if '[' in rest:
                bracket_pos = rest.find('[')
                key_name = rest[:bracket_pos]
                nested_content = rest[bracket_pos + 1:-1]
                is_many = True
            elif '{' in rest:
                brace_pos = rest.find('{')
                key_name = rest[:brace_pos]
                nested_content = rest[brace_pos + 1:-1]
                is_many = False
            else:
                raise ValueError(f"Invalid relation format: {token}")
        
        # Parser le contenu nested
        nested_result = {
            'model': model_name,
            'fields': [],
            'relations': {}
        }
        
        if nested_content.strip():
            # Enlever les accolades externes si présentes (cas relation many)
            if nested_content.strip().startswith('{') and nested_content.strip().endswith('}'):
                nested_content = nested_content.strip()[1:-1]
            
            self._parse_fields_content(nested_content, nested_result)
        
        # Créer l'objet relation
        relation_data = {
            'model': model_name,
            'fields': nested_result['fields'],
            'relations': nested_result['relations'],
            'is_many': is_many
        }
        
        if function_info:
            relation_data['function'] = function_info
            
        result['relations'][key_name] = relation_data
        
    def get_queryset(self):
        """Retourne le queryset optimisé avec select_related et prefetch_related"""
        # Récupérer le modèle principal
        model_class = self._get_model_by_name(self.parsed_data['model'])
        if not model_class:
            raise ValueError(f"Model '{self.parsed_data['model']}' not found")
        
        # Construire les optimisations
        select_related, prefetch_related = self._build_optimizations(self.parsed_data, "")
        
        # Appliquer les optimisations au queryset
        queryset = model_class.objects.all()
        
        if select_related:
            queryset = queryset.select_related(*select_related)
        
        if prefetch_related:
            queryset = queryset.prefetch_related(*prefetch_related)
        
        return queryset
    
    def _build_optimizations(self, data, current_path):
        """Construit récursivement les optimisations avec Prefetch avancés"""
        select_related = []
        prefetch_related = []
        
        for relation_key, relation_info in data.get('relations', {}).items():
            # Construire le chemin complet
            if current_path:
                full_path = f"{current_path}__{relation_key}"
            else:
                full_path = relation_key
            
            # Récupérer le modèle lié
            related_model = self._get_model_by_name(relation_info['model'])
            
            # Gérer les fonctions (max, min, count)
            if relation_info.get('function'):
                func_info = relation_info['function']
                func_name = func_info['name']
                func_field = func_info.get('field')
                
                if func_name in ['max', 'min']:                    
                    filtered_queryset = related_model.objects.order_by(f'-{func_field}' if func_name == 'max' else func_field)
                    
                    # Appliquer les optimisations nested
                    nested_select, nested_prefetch = self._build_optimizations(relation_info, "")
                    
                    if nested_select:
                        filtered_queryset = filtered_queryset.select_related(*nested_select)
                    if nested_prefetch:
                        filtered_queryset = filtered_queryset.prefetch_related(*nested_prefetch)
                
                if func_name == "count":
                    filtered_queryset = related_model.objects.all()
                    
                prefetch_obj = Prefetch(full_path, queryset=filtered_queryset)
                prefetch_related.append(prefetch_obj)
            
            elif relation_info['is_many']:
                # Relation many -> Prefetch avec optimisations internes
                nested_select, nested_prefetch = self._build_optimizations(relation_info, "")
                
                # Créer un Prefetch optimisé
                optimized_queryset = related_model.objects.all()
                if nested_select:
                    optimized_queryset = optimized_queryset.select_related(*nested_select)
                if nested_prefetch:
                    optimized_queryset = optimized_queryset.prefetch_related(*nested_prefetch)
                
                prefetch_obj = Prefetch(full_path, queryset=optimized_queryset)
                prefetch_related.append(prefetch_obj)
                    
            else:
                # Relation single (1:1 ou FK)
                select_related.append(full_path)
                
                # Continuer récursivement pour les relations nested
                nested_select, nested_prefetch = self._build_optimizations(
                    relation_info, full_path
                )
                select_related.extend(nested_select)
                prefetch_related.extend(nested_prefetch)
        
        return select_related, prefetch_related

    @classmethod
    def _get_model_by_name(cls, model_name):
        """Récupère un modèle par son nom"""
        try:
            # Chercher dans toutes les apps
            for app_config in apps.get_app_configs():
                try:
                    return app_config.get_model(model_name.lower())
                except LookupError:
                    continue
            return None
        except Exception:
            return None

class QueryLangSerializer(serializers.ModelSerializer):
    """
    Serializer full dynamique qui parse des query strings comme:
    Agent{"nom", "prenom", Contrat:contrats[{"date_debut"}]}
    User{"email", Profile:profile{"bio", "avatar"}, Post:articles[{"title", "date_creation"}]}
    """
    
    def __new__(cls, *args, **kwargs):
        context = kwargs.get('context', {})
        qlp = context.get('query_lang_parser')
        if qlp:
            try:
                # Générer la classe
                dynamic_class = cls._generate_serializer_class(qlp.parsed_data)
                return dynamic_class(*args, **kwargs)
                
            except Exception as e:
                raise ValidationError(f"Invalid query format: {str(e)}")
        
        return super().__new__(cls)
    
    @classmethod
    def _generate_serializer_class(cls, parsed):
        """Génère une classe de serializer à partir de la structure parsée"""
        # Récupérer le modèle
        modelCls = QueryLangParser._get_model_by_name(parsed['model'])
        if not modelCls:
            raise ValidationError(f"Model '{parsed['model']}' not found")
        
        # Préparer les attributs de classe
        attrs = {}
        
        # Ajouter les relations
        for relation_key, relation_info in parsed['relations'].items():
            if relation_info.get('function'):
                # Gérer les fonctions (max, min, count)
                func_info = relation_info['function']
                func_name = func_info['name']
                
                if func_name == 'count':
                    # Count retourne juste le nombre
                    def make_count_method(rel_key):
                        def get_count(self, obj):
                            return len(getattr(obj, rel_key).all())
                        return get_count
                    
                    attrs[relation_key] = serializers.SerializerMethodField()
                    attrs[f'get_{relation_key}'] = make_count_method(relation_key)
                elif func_name in ['min', 'max']:
                    # max/min retournent des objets sérialisés                    
                    def make_getter(serializer_cls, rel_key):
                        def getter(self, obj):
                            rel = list(getattr(obj, rel_key).all())
                            return serializer_cls(rel[0], read_only=True).data if rel else None
                        return getter
                        
                    attrs[relation_key] = serializers.SerializerMethodField()
                    nested_serializer_class = cls._generate_serializer_class(relation_info)
                    attrs[f"get_{relation_key}"] = make_getter(nested_serializer_class, relation_key)
            else:
                # Relations normales
                nested_serializer_class = cls._generate_serializer_class(relation_info)
                attrs[relation_key] = nested_serializer_class(
                    many=relation_info['is_many'], 
                    read_only=True
                )
        
        # Créer la classe Meta
        class Meta:
            model = modelCls
            fields = (parsed['fields'] + list(parsed['relations'].keys())) or ["pk"]
        
        attrs['Meta'] = Meta
        
        # Générer la classe dynamiquement
        return type(
            f'{modelCls.__name__}DynamicSerializer',
            (serializers.ModelSerializer,),
            attrs
        )

def filter_queryset(request, queryset):
    query_params = request.query_params
    filter_dict = {}
    SPECIAL_KEYWORDS = { "exist", "query" }
    
    if len(query_params) == 0:
        return queryset
    for key, value in query_params.items():
        if key in SPECIAL_KEYWORDS:
            continue
        if any(k in key for k in api_settings.UNAUTHORIZED_KEYS): raise QueryLangException(f'Unauthorized key: {key}', 'forbidden_filtering_key')
        if key.endswith("__in"):
            #Définition d'un caractère de séparation qu'on a (très) peu de chance de rencontrer
            filter_dict[key] = value.split("::")
        else:
            filter_dict[key] = value
    try:
        return queryset.filter(**filter_dict)
    except FieldError:
        return queryset.none()