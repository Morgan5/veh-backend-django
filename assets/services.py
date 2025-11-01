"""
Services pour la génération d'assets (images et sons) via IA
"""
import os
import io
import uuid
import json
import requests
from typing import Optional, Tuple
from gtts import gTTS
from PIL import Image
from decouple import config
# Essayer d'importer les bibliothèques optionnelles pour la génération musicale
try:
    from transformers import AutoProcessor, MusicgenForConditionalGeneration
    import torch
    import scipy.io.wavfile
    import numpy as np
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    # Définir pour éviter les erreurs de référence
    scipy = None
    np = None

# Cache pour les modèles MusicGen (évite de recharger le modèle à chaque génération)
_model_cache = {}
_processor_cache = {}


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
    
    def generate_ambient_music(self, description: str, duration: int = 15) -> Tuple[bytes, dict]:
        """
        Génère une musique d'ambiance à partir d'une description textuelle
        
        Utilise MusicGen via Transformers localement avec mise en cache du modèle
        pour accélérer les générations successives. Le modèle sera téléchargé 
        automatiquement au premier usage.
        
        Args:
            description: Description de l'ambiance musicale souhaitée (ex: "dark mysterious castle music")
            duration: Durée en secondes (par défaut 15s pour accélérer, max recommandé: 30s)
        
        Returns:
            Tuple contenant (audio_bytes, metadata)
            
        Raises:
            Exception: Si les bibliothèques nécessaires ne sont pas installées ou en cas d'erreur
        """
        if not TRANSFORMERS_AVAILABLE:
            raise Exception(
                "Les bibliothèques 'transformers' et 'torch' sont requises pour la génération musicale.\n"
                "Installez-les avec: pip install transformers torch scipy numpy"
            )
        
        # Vérifier si un GPU est disponible
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model_name = config('MUSICGEN_MODEL', default='facebook/musicgen-small')
        
        try:
            # Utiliser le cache du modèle pour éviter de le recharger à chaque fois
            cache_key = f"{model_name}_{device}"
            
            if cache_key not in _model_cache:
                # Charger le modèle seulement la première fois
                processor = AutoProcessor.from_pretrained(model_name)
                model = MusicgenForConditionalGeneration.from_pretrained(model_name)
                model.to(device)
                model.eval()  # Mode évaluation pour optimiser les performances
                
                # Compiler le modèle si PyTorch 2.0+ est disponible et sur GPU
                if hasattr(torch, 'compile') and device == "cuda":
                    try:
                        model = torch.compile(model, mode="reduce-overhead")
                    except Exception:
                        pass  # Si compilation échoue, continuer sans compilation
                
                _processor_cache[cache_key] = processor
                _model_cache[cache_key] = model
            else:
                # Réutiliser le modèle depuis le cache (gain de temps énorme!)
                processor = _processor_cache[cache_key]
                model = _model_cache[cache_key]
            
            # Réduire la durée pour accélérer (15s au lieu de 30s par défaut)
            # Cela réduit significativement le temps de génération
            max_duration = min(duration, 15)
            
            inputs = processor(
                text=[description],
                padding=True,
                return_tensors="pt",
            ).to(device)
            
            # Générer la musique avec des paramètres optimisés
            # max_new_tokens contrôle la durée approximative (~45 tokens par seconde)
            max_new_tokens = int(max_duration * 45)
            
            with torch.no_grad():
                audio_values = model.generate(
                    **inputs, 
                    max_new_tokens=max_new_tokens, 
                    do_sample=True,
                    temperature=1.0,
                    top_k=250,
                    guidance_scale=3.0
                )
            
            # Récupérer l'audio généré
            sampling_rate = model.config.audio_encoder.sampling_rate
            audio_array = audio_values[0, 0].cpu().numpy()
            
            # Normaliser l'audio si nécessaire
            if audio_array.max() > 1.0 or audio_array.min() < -1.0:
                audio_array = np.clip(audio_array, -1.0, 1.0)
            
            # Convertir en int16 pour le format WAV
            audio_int16 = (audio_array * 32767).astype(np.int16)
            
            # Sauvegarder dans un buffer mémoire au format WAV
            audio_buffer = io.BytesIO()
            scipy.io.wavfile.write(audio_buffer, sampling_rate, audio_int16)
            audio_bytes = audio_buffer.getvalue()
            audio_buffer.close()
            
            metadata = {
                "duration": max_duration,
                "sampling_rate": int(sampling_rate),
                "type": "music",
                "model": model_name,
                "description": description,
                "device": device,
                "format": "wav"
            }
            
            return audio_bytes, metadata
            
        except Exception as e:
            error_msg = str(e)
            if "out of memory" in error_msg.lower() or "cuda" in error_msg.lower():
                raise Exception(
                    f"Erreur GPU/Mémoire: {error_msg}\n"
                    "Solutions:\n"
                    "1. Utilisez le modèle 'musicgen-small' (plus léger)\n"
                    "2. Réduisez la durée de génération\n"
                    "3. Utilisez CPU (plus lent mais fonctionne): device='cpu'"
                )
            elif "download" in error_msg.lower() or "connection" in error_msg.lower():
                raise Exception(
                    f"Erreur de téléchargement du modèle: {error_msg}\n"
                    "Vérifiez votre connexion internet et votre token Hugging Face si nécessaire."
                )
            else:
                raise Exception(f"Erreur lors de la génération musicale: {error_msg}")


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
