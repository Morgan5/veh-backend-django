"""
Services pour la génération d'assets (images et sons) via IA
"""
import os
import io
import uuid
import requests
from typing import Optional, Tuple
from gtts import gTTS
from PIL import Image
from decouple import config


class ImageGenerationService:
    """
    Service pour générer des images via Hugging Face Inference API
    Utilise Stable Diffusion pour générer des images à partir de descriptions textuelles
    """
    
    def __init__(self):
        self.api_token = config('HUGGINGFACE_API_TOKEN', default=None)
        # Modèle par défaut : Stable Diffusion XL pour de meilleures images
        self.default_model = config('HF_IMAGE_MODEL', default='stabilityai/stable-diffusion-xl-base-1.0')
        self.base_url = "https://api-inference.huggingface.co/models"
    
    def generate(self, prompt: str, negative_prompt: Optional[str] = None) -> Tuple[bytes, dict]:
        """
        Génère une image à partir d'une description textuelle
        
        Args:
            prompt: Description textuelle de l'image à générer
            negative_prompt: Éléments à éviter dans l'image (optionnel)
        
        Returns:
            Tuple contenant (image_bytes, metadata) ou None si erreur
        """
        if not self.api_token:
            raise ValueError("HUGGINGFACE_API_TOKEN non configuré dans les variables d'environnement")
        
        url = f"{self.base_url}/{self.default_model}"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "num_inference_steps": 30,
                "guidance_scale": 7.5,
            }
        }
        
        if negative_prompt:
            payload["parameters"]["negative_prompt"] = negative_prompt
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                image_bytes = response.content
                
                # Obtenir les métadonnées de l'image
                image = Image.open(io.BytesIO(image_bytes))
                width, height = image.size
                
                metadata = {
                    "width": width,
                    "height": height,
                    "format": image.format.lower() if image.format else "png",
                    "model": self.default_model,
                    "prompt": prompt
                }
                
                return image_bytes, metadata
            elif response.status_code == 503:
                # Modèle en cours de chargement, réessayer après un délai
                raise Exception("Le modèle est en cours de chargement. Veuillez réessayer dans quelques instants.")
            else:
                error_msg = response.json().get("error", "Erreur lors de la génération de l'image")
                raise Exception(f"Erreur API Hugging Face: {error_msg}")
                
        except requests.exceptions.Timeout:
            raise Exception("Timeout lors de la génération de l'image. Le service est peut-être surchargé.")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erreur de connexion: {str(e)}")


class SoundGenerationService:
    """
    Service pour générer des sons et musiques d'ambiance
    Utilise gTTS pour la synthèse vocale et peut étendre à d'autres services
    """
    
    def __init__(self):
        self.hf_api_token = config('HUGGINGFACE_API_TOKEN', default=None)
    
    def generate_text_to_speech(self, text: str, lang: str = 'fr', slow: bool = False) -> Tuple[bytes, dict]:
        """
        Génère un fichier audio à partir d'un texte (Text-to-Speech)
        Idéal pour la narration ou les descriptions audio des scènes
        
        Args:
            text: Texte à convertir en audio
            lang: Langue du texte (par défaut 'fr' pour français)
            slow: Si True, parle plus lentement
        
        Returns:
            Tuple contenant (audio_bytes, metadata)
        """
        try:
            # Créer l'objet gTTS
            tts = gTTS(text=text, lang=lang, slow=slow)
            
            # Générer l'audio dans un buffer mémoire
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_bytes = audio_buffer.getvalue()
            audio_buffer.seek(0)
            
            # Estimer la durée (approximation: ~150 mots/min en français)
            words_count = len(text.split())
            estimated_duration = int((words_count / 150) * 60)  # en secondes
            
            metadata = {
                "duration": estimated_duration,
                "language": lang,
                "type": "speech",
                "words_count": words_count
            }
            
            return audio_bytes, metadata
            
        except Exception as e:
            raise Exception(f"Erreur lors de la génération audio: {str(e)}")
    
    def generate_ambient_music(self, description: str, duration: int = 30) -> Tuple[bytes, dict]:
        """
        Génère une musique d'ambiance à partir d'une description textuelle
        Utilise Hugging Face MusicGen si le token est disponible, sinon retourne None
        
        Args:
            description: Description de l'ambiance musicale souhaitée
            duration: Durée en secondes (par défaut 30s)
        
        Returns:
            Tuple contenant (audio_bytes, metadata) ou None si non disponible
        """
        if not self.hf_api_token:
            # Si pas de token, on ne peut pas générer de musique
            raise Exception("HUGGINGFACE_API_TOKEN requis pour la génération musicale")
        
        # Modèle MusicGen de Meta sur Hugging Face
        model = "facebook/musicgen-small"
        url = f"https://api-inference.huggingface.co/models/{model}"
        headers = {
            "Authorization": f"Bearer {self.hf_api_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": description,
            "parameters": {
                "duration": duration
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            
            if response.status_code == 200:
                audio_bytes = response.content
                metadata = {
                    "duration": duration,
                    "type": "music",
                    "model": model,
                    "description": description
                }
                return audio_bytes, metadata
            elif response.status_code == 503:
                raise Exception("Le modèle est en cours de chargement. Veuillez réessayer dans quelques instants.")
            else:
                error_msg = response.json().get("error", "Erreur lors de la génération musicale")
                raise Exception(f"Erreur API Hugging Face: {error_msg}")
                
        except requests.exceptions.Timeout:
            raise Exception("Timeout lors de la génération musicale. Le service est peut-être surchargé.")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erreur de connexion: {str(e)}")


class AssetStorageService:
    """
    Service pour stocker les fichiers générés localement ou dans un service cloud
    """
    
    def __init__(self):
        from django.conf import settings
        # Utiliser MEDIA_ROOT depuis les settings Django
        # Si MEDIA_ROOT est un chemin relatif, le joindre à BASE_DIR
        base_media = getattr(settings, 'MEDIA_ROOT', 'media')
        if not os.path.isabs(base_media):
            # Si c'est un chemin relatif, le joindre à BASE_DIR
            base_dir = getattr(settings, 'BASE_DIR', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            base_media = os.path.join(base_dir, base_media)
        self.media_root = os.path.join(base_media, 'assets')
        # Créer le dossier s'il n'existe pas
        os.makedirs(self.media_root, exist_ok=True)
    
    def save_image(self, image_bytes: bytes, filename: str) -> str:
        """
        Sauvegarde une image et retourne l'URL relative
        
        Args:
            image_bytes: Bytes de l'image
            filename: Nom du fichier (avec extension)
        
        Returns:
            URL relative du fichier sauvegardé
        """
        filepath = os.path.join(self.media_root, filename)
        
        with open(filepath, 'wb') as f:
            f.write(image_bytes)
        
        # Retourner l'URL relative (sera servi via Django media)
        return f"/media/assets/{filename}"
    
    def save_audio(self, audio_bytes: bytes, filename: str) -> str:
        """
        Sauvegarde un fichier audio et retourne l'URL relative
        
        Args:
            audio_bytes: Bytes de l'audio
            filename: Nom du fichier (avec extension)
        
        Returns:
            URL relative du fichier sauvegardé
        """
        filepath = os.path.join(self.media_root, filename)
        
        with open(filepath, 'wb') as f:
            f.write(audio_bytes)
        
        return f"/media/assets/{filename}"
