# backend/apps/beams/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import BeamInputSerializer
from .engine import run_calculation

class BeamCalcView(APIView):
    def post(self, request):
        s = BeamInputSerializer(data=request.data)
        if not s.is_valid():
            return Response({"valid": False, "errors": s.errors}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = run_calculation(s.validated_data)
        except ValueError as e:
            return Response({"valid": False, "errors": {"placement": str(e)}}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"valid": False, "errors": {"server": str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(result, status=status.HTTP_200_OK)
