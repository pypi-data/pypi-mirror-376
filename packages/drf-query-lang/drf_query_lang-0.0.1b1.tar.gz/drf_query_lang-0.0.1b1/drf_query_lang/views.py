from rest_framework.views import APIView
from rest_framework.response import Response

from .query_lang import QueryLangParser, QueryLangSerializer, filter_queryset
from .settings import api_settings

from logging import getLogger

logger = getLogger(__name__)

class QueryLangView(APIView):
    def get(self, request):
        if not api_settings.AUTHORIZATION_METHOD(request):
            logger.warning(
                f"[Lang Query refusé] - Utilisateur non autorisé ({request.user}) a tenté : {dict(request.query_params)}"
            )
            return Response({'detail': 'Vous ne pouvez pas utiliser le query lang.'}, status=403)
        
        query_param = request.query_params.get('query')
        if not query_param:
            return Response(
                {'detail': 'Missing required parameter: query'}, 
                status=400
            )
        
        parser = QueryLangParser(query_param)
        filtered_queryset = filter_queryset(request, parser.get_queryset())
                
        if request.query_params.get("exist") == "true":
            return Response({
                "exist": filtered_queryset.exists()
            })
            
        serializer = QueryLangSerializer(
                filtered_queryset,
                read_only=True,
                many=True,
                context={'query_lang_parser': parser}
            )
        return Response(serializer.data)