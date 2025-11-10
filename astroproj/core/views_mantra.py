from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import parser_classes
from .mantra_utils import analyze_mantra_prunciation

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def analyze_mantra(request):
    if 'audio' not in request.FILES:
        return Response({'error': 'No audio file provided'}, status=400)
    
    if 'mantra' not in request.data:
        return Response({'error': 'No mantra text provided'}, status=400)
    
    audio_file = request.FILES['audio']
    expected_mantra = request.data['mantra']
    
    result = analyze_mantra_prunciation(audio_file, expected_mantra)
    
    return Response(result)