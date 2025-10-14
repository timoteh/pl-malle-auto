import pyautogui
import cv2
import numpy as np
import time
import threading
import sys
from PIL import Image
import os
import keyboard
import tkinter as tk

# Configuration
TOTAL_LOOP = 0 
IMAGE_LEVEL = "./images/image_lvl.PNG"
IMAGE_JOIN = "./images/image_join_2.PNG"
IMAGE_OUT_FIGHT = "./images/image_out.PNG"  # Chemin vers l'image à détecter si hors combat
IMAGE_IN_FIGHT = "./images/image_fight.PNG"  # Chemin vers l'image à détecter si hors combat
OUT_FIGHT_REGION = (655, 961, 31, 29)  # Zone à surveiller (x, y, largeur, hauteur)
IN_FIGHT_REGION = (655, 961, 31, 29)  # Zone pour la deuxième image (optionnel, sinon même que OUT_FIGHT_REGION)
LVL_REGION = (841, 342, 156, 30) # (x, y, largeur, hauteur)
#JOIN_REGION = (70, 476, 214, 88) # (x, y, largeur, hauteur)
JOIN_REGION = (8, 492, 36, 39) # (x, y, largeur, hauteur)
CONFIDENCE = 0.7  # Seuil de confiance pour la détection (0.0 à 1.0)
LVL_CONFIDENCE = 0.6  # Seuil de confiance pour le level up (plus strict pour éviter les faux positifs)
CHECK_INTERVAL = 3  # Intervalle en secondes entre chaque vérification
SECOND_CHECK_DELAY = 15  # Délai avant de reprendre la loop principale après détection de la 2ème image
TIMEOUT_THRESHOLD = 30  # Seuil en secondes pour détecter un blocage
DEBUG_MODE = False  # Active les messages de debug détaillés

RESTART_CLICK_POSITIONS = [
    (1898, 10),
    (293, 450),
    (1034, 568)
]

# Coordonnées où cliquer quand l'image est détectée
RESTART_DUNGEON_CLICK_POSITIONS = [
    (874, 371),  
    (1111, 418), 
    (582, 329), 
    (836, 391),  
    (1030, 441), 
    (1030, 441)
]

IN_FIGHT_CLICK_POSITIONS = [
    (1384, 977)  # Passe tour si besoin
]

JOIN_CLICK_POSITIONS = [
    (170, 535)  # Premier clic pour rejoindre
]

LVL_UP_CLICK = [
    (968, 800)
] # Click si level up

# Variables globales pour le monitoring
last_check_time = time.time()
is_running = True
check_counter = 0
template_cache = {}  # Cache pour les images templates
start_time = time.time()  # Temps de départ pour le restart
watchdog_thread_ref = None  # Référence au thread watchdog
fight_counter = 1  # Compteur de fights
counter_window = None  # Référence à la fenêtre du compteur

# Délai entre chaque clic (en secondes)
CLICK_DELAY = 2.5  # 2.5 secondes
CLICK_DELAY_SMALLER = 1.5  # 1.5 secondes

# Variables globales pour le monitoring
last_check_time = time.time()
is_running = True
check_counter = 0

def debug_print(message):
    """Affiche un message de debug avec timestamp si le mode debug est activé"""
    if DEBUG_MODE:
        timestamp = time.strftime('%H:%M:%S')
        print(f"[{timestamp}] DEBUG: {message}")

class CounterOverlay:
    """Classe pour gérer l'overlay du compteur"""
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()  # Cacher la fenêtre principale
        
        # Créer une fenêtre toplevel pour le compteur
        self.window = tk.Toplevel(self.root)
        self.window.overrideredirect(True)  # Enlever les bordures
        self.window.attributes('-topmost', True)  # Toujours au-dessus
        self.window.configure(bg='black')  # Fond noir
        
        # Positionner en haut à droite
        screen_width = self.window.winfo_screenwidth()
        window_width = 200
        window_height = 80
        x = screen_width - window_width - 10
        y = 100
        self.window.geometry(f'{window_width}x{window_height}+{x}+{y}')
        
        # Label pour le compteur
        self.counter_label = tk.Label(
            self.window,
            text="1",
            font=('Arial', 24, 'bold'),
            fg='lime',
            bg='black'
        )
        self.counter_label.pack(expand=True)
        
        # Afficher la fenêtre
        self.window.deiconify()
    
    def update_counter(self, value):
        """Met à jour la valeur du compteur"""
        self.counter_label.config(text=str(value))
    
    def update(self):
        """Met à jour la fenêtre tkinter"""
        try:
            self.root.update()
        except:
            pass

def create_counter_overlay():
    """Crée l'overlay du compteur dans un thread séparé"""
    global counter_window
    counter_window = CounterOverlay()
    debug_print("Overlay du compteur créé")

def update_fight_counter():
    """Incrémente le compteur de fights et met à jour l'affichage"""
    global fight_counter, counter_window
    fight_counter += 1
    print(f"⚔️ Fight #{fight_counter}")
    
    if counter_window:
        counter_window.update_counter(fight_counter)
        counter_window.update()

def watchdog_thread():
    """Thread de surveillance qui vérifie si le script principal fonctionne"""
    global last_check_time, is_running
    
    while is_running:
        current_time = time.time()
        time_since_last_check = current_time - last_check_time
        
        if time_since_last_check > TIMEOUT_THRESHOLD:
            print(f"\n⚠️  ATTENTION: Aucune activité détectée depuis {time_since_last_check:.1f}s")
            print("Le script semble bloqué. Tentative de redémarrage automatique...")
            # Reset du timer
            last_check_time = current_time
            
        time.sleep(5)  # Vérification toutes les 5 secondes

def load_template_image(image_path):
    """Charge l'image template à détecter"""
    try:
        debug_print(f"Tentative de chargement de l'image: {image_path}")
        
        # Vérifier si le fichier existe
        if not os.path.exists(image_path):
            print(f"❌ Le fichier {image_path} n'existe pas")
            return None
        
        template = cv2.imread(image_path, cv2.IMREAD_COLOR)
        if template is None:
            raise ValueError(f"Impossible de charger l'image: {image_path}")
        
        # Afficher les dimensions de l'image chargée
        height, width = template.shape[:2]
        debug_print(f"✅ Image {image_path} chargée avec succès - Dimensions: {width}x{height}")
        
        return template
    except Exception as e:
        print(f"❌ Erreur lors du chargement de l'image {image_path}: {e}")
        return None
    
def safe_screenshot_region(region, max_retries=3):
    """Capture d'écran avec gestion des erreurs et retry automatique"""
    for attempt in range(max_retries):
        try:
            debug_print(f"Tentative de capture d'écran {attempt + 1}/{max_retries}")
            # Petit délai pour éviter les problèmes de timing
            time.sleep(0.1)
            screenshot = pyautogui.screenshot(region=region)
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            debug_print("Capture d'écran réussie")
            return screenshot_cv
        except Exception as e:
            debug_print(f"Erreur capture tentative {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(0.5)  # Attente avant retry
            else:
                print(f"Erreur persistante lors de la capture d'écran: {e}")
                return None

def capture_screen_region(region):
    """Capture une région spécifique de l'écran avec amélioration de stabilité"""
    return safe_screenshot_region(region)

def save_debug_screenshot(screenshot, region, image_name, confidence, brightness):
    """Sauvegarde une capture d'écran pour debug"""
    try:
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        filename = f"debug_{image_name}_{timestamp}_conf{confidence:.3f}_bright{brightness:.1f}.png"
        #cv2.imwrite(filename, screenshot)
        #print(f"📸 Capture debug sauvegardée: {filename}")
    except Exception as e:
        print(f"Erreur sauvegarde debug: {e}")

def detect_image_in_region(template, region, image_name="", confidence_threshold=None):
    """Détecte si l'image template est présente dans la région spécifiée"""
    global last_check_time, check_counter
    
    # Utiliser le seuil de confiance personnalisé ou le seuil par défaut
    if confidence_threshold is None:
        confidence_threshold = CONFIDENCE
    
    # Mise à jour du timestamp
    last_check_time = time.time()
    if image_name == "":  # Ne compter que pour l'image hors combat
        check_counter += 1
    
    debug_print(f"Début détection {image_name} #{check_counter if image_name == '' else 'N/A'} (seuil: {confidence_threshold:.2f})")
    
    screenshot = capture_screen_region(region)
    if screenshot is None or template is None:
        debug_print(f"Échec capture ou template manquant pour {image_name}")
        return False
    
    try:
        # Vérification de la luminosité moyenne de la zone
        gray_screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        avg_brightness = np.mean(gray_screenshot)
        
        # Si la zone est trop sombre (noire), ne pas détecter
        if avg_brightness < 30:  # Seuil pour considérer la zone comme noire
            debug_print(f"❌ Zone trop sombre pour {image_name} (luminosité: {avg_brightness:.1f})")
            return False
        
        # Détection par template matching avec plusieurs méthodes
        debug_print(f"Exécution du template matching pour {image_name}...")
        
        # Méthode 1: TM_CCOEFF_NORMED (la plus fiable)
        result1 = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        min_val1, max_val1, min_loc1, max_loc1 = cv2.minMaxLoc(result1)
        
        # Méthode 2: TM_SQDIFF_NORMED (plus stricte pour les zones noires)
        result2 = cv2.matchTemplate(screenshot, template, cv2.TM_SQDIFF_NORMED)
        min_val2, max_val2, min_loc2, max_loc2 = cv2.minMaxLoc(result2)
        
        # Pour TM_SQDIFF_NORMED, on cherche la valeur minimale (plus proche de 0 = meilleure correspondance)
        # Convertir en score de confiance (1 - min_val2)
        confidence2 = 1 - min_val2
        
        # Utiliser seulement les deux méthodes les plus fiables
        final_confidence = (max_val1 + confidence2) / 2
        
        debug_print(f"TM_CCOEFF_NORMED: {max_val1:.3f}, TM_SQDIFF_NORMED: {confidence2:.3f}, Final: {final_confidence:.3f}")
        
        # Vérification supplémentaire : les deux méthodes doivent être au-dessus d'un seuil minimum
        min_individual_threshold = confidence_threshold * 0.8  # 80% du seuil principal
        if max_val1 < min_individual_threshold or confidence2 < min_individual_threshold:
            debug_print(f"❌ Une des méthodes sous le seuil minimum ({min_individual_threshold:.3f})")
            return False
        
        # Vérification si la correspondance dépasse le seuil de confiance
        if final_confidence >= confidence_threshold:
            # Si la zone est sombre mais qu'on détecte quelque chose, sauvegarder pour debug
            if avg_brightness < 50:
                save_debug_screenshot(screenshot, region, image_name, final_confidence, avg_brightness)
            
            print(f"✅ {image_name} détectée avec confiance: {final_confidence:.3f} (luminosité: {avg_brightness:.1f})")
            return True
        else:
            # Sauvegarder si la confiance est élevée mais pas assez pour déclencher
            if final_confidence > confidence_threshold * 0.8:  # 80% du seuil
                save_debug_screenshot(screenshot, region, image_name, final_confidence, avg_brightness)
            
            debug_print(f"❌ {image_name} non détectée (confiance: {final_confidence:.3f}, luminosité: {avg_brightness:.1f})")
            return False
            
    except Exception as e:
        print(f"Erreur lors de la détection {image_name}: {e}")
        debug_print(f"Stack trace: {sys.exc_info()}")
        return False

def perform_level_up_click():
    """Effectue l'appui sur Escape pour le level up"""
    print("🎯 Level up détecté ! Appui sur Escape...")
        
    try:
        print("Appui sur la touche Escape (méthode 1: press)")
        keyboard.press_and_release('esc')
        time.sleep(1)
        
    except Exception as e:
        print(f"Erreur lors de l'appui sur Escape: {e}")
    
    print("✅ Appui sur Escape terminé.")

def perform_restart_dungeon():
    print("🎯 Image hors combat détectée ! Exécution des clics...")
    
    for i, (x, y) in enumerate(RESTART_DUNGEON_CLICK_POSITIONS, 1):
        try:
            print(f"Clic {i} à la position ({x}, {y})")
            pyautogui.click(x, y)
            # Utiliser un délai plus court pour les positions 0, 1, 4 et 5
            delay = CLICK_DELAY_SMALLER if i in [0, 1, 4, 5] else CLICK_DELAY
            time.sleep(delay)
        except Exception as e:
            print(f"Erreur lors du clic {i}: {e}")
    
    print("✅ Séquence de clics terminée.")

def perform_join_click():
    """Effectue le clic pour rejoindre"""
    print("🎯 Image join détectée ! Exécution du clic...")
    
    for i, (x, y) in enumerate(JOIN_CLICK_POSITIONS, 1):
        try:
            print(f"Clic join {i} à la position ({x}, {y})")
            pyautogui.click(x, y)
            time.sleep(CLICK_DELAY)
        except Exception as e:
            print(f"Erreur lors du clic join {i}: {e}")
    
    print("✅ Clic join terminé.")

def perform_restart_sequence():
    global start_time, is_running, watchdog_thread_ref
    
    print("\n🔄 Séquence de restart - 30 minutes écoulées !")
    print("🎯 Exécution de la séquence de clics de restart...")
    
    try:
        # Clic 1
        x1, y1 = RESTART_CLICK_POSITIONS[0]
        print(f"Clic restart 1 à la position ({x1}, {y1})")
        pyautogui.click(x1, y1)
        print("⏳ Attente de 3 secondes...")
        time.sleep(3)
        
        # Clic 2
        x2, y2 = RESTART_CLICK_POSITIONS[1]
        print(f"Clic restart 2 à la position ({x2}, {y2})")
        pyautogui.click(x2, y2)
        print("⏳ Attente de 12 secondes...")
        time.sleep(12)
        
        # Clic 3
        x3, y3 = RESTART_CLICK_POSITIONS[2]
        print(f"Clic restart 3 à la position ({x3}, {y3})")
        pyautogui.click(x3, y3)
        
    except Exception as e:
        print(f"❌ Erreur lors de la séquence de restart: {e}")
    
    print("✅ Séquence de restart terminée.")
    print("🔄 Arrêt propre du thread de surveillance...")
    
    # Arrêter le thread de surveillance proprement
    is_running = False
    
    # Attendre que le thread watchdog se termine (max 10 secondes)
    if watchdog_thread_ref and watchdog_thread_ref.is_alive():
        watchdog_thread_ref.join(timeout=10)
        if watchdog_thread_ref.is_alive():
            print("⚠️ Le thread watchdog n'a pas pu se terminer proprement")
        else:
            print("✅ Thread watchdog terminé proprement")
    
    print("🔄 Réinitialisation complète du script dans 2 secondes...")
    time.sleep(2)
    
    # Relancer le script Python depuis le début
    # os.execv() remplace COMPLÈTEMENT le processus actuel :
    # - Même PID, mais nouvelle image mémoire
    # - Tous les threads/variables/connexions sont terminés
    # - Le script redémarre comme si on l'avait lancé à nouveau
    print("🚀 Redémarrage du script...\n")
    os.execv(sys.executable, ['python'] + sys.argv)

def perform_fight_sequence(second_template):
    global start_time
    
    # Incrémenter le compteur de fights
    update_fight_counter()
    
    print("\n⚔️ Début de la séquence de combat...")
    
    # Attendre que la deuxième image soit présente
    print("🔍 Attente de l'image de combat...")
    while is_running:
        second_image_detected = detect_image_in_region(
            second_template, 
            IN_FIGHT_REGION,
            "Image de combat"
        )
        
        if second_image_detected:
            print("🎉 Image de combat détectée !")
            break
        
        print("⏳ Image de combat non détectée, nouvelle vérification dans 3 secondes...")
        time.sleep(3)
    
    if not is_running:
        return
    
    # Vérifier le temps écoulé depuis le départ
    elapsed_time = time.time() - start_time
    elapsed_minutes = elapsed_time / 60
    
    print(f"⏱️ Temps écoulé : {elapsed_minutes:.1f} minutes")
    
    # Si 30 minutes ou plus se sont écoulées, lancer la séquence de restart
    if elapsed_minutes >= 30:
        perform_restart_sequence()
    

def test_level_up_detection(level_template):
    """Test de détection de l'image level up pour diagnostiquer les problèmes"""
    print("\n🔬 Test de détection de l'image level up...")
    print(f"Zone de test: {LVL_REGION}")
    
    # Capture d'écran de la zone
    screenshot = capture_screen_region(LVL_REGION)
    if screenshot is None:
        print("❌ Impossible de capturer la zone de test")
        return False
    
    # Sauvegarder la capture pour debug
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    debug_filename = f"debug_test_level_up_{timestamp}.png"
    #cv2.imwrite(debug_filename, screenshot)
    #print(f"📸 Capture de test sauvegardée: {debug_filename}")
    
    # Test avec différents seuils
    thresholds = [0.3, 0.4, 0.5, 0.6, 0.7]
    for threshold in thresholds:
        detected = detect_image_in_region(level_template, LVL_REGION, f"Test (seuil {threshold})", threshold)
        if detected:
            print(f"✅ Détection réussie avec seuil {threshold}")
            return True
        else:
            print(f"❌ Pas de détection avec seuil {threshold}")
    
    return False

def main():
    """Fonction principale du script"""
    global is_running, last_check_time, start_time
    
    print("🚀 Démarrage du script de surveillance d'écran avec logique prioritaire...")
    print(f"Image level up: {IMAGE_LEVEL}")
    print(f"Image hors combat: {IMAGE_OUT_FIGHT}")
    print(f"Image de combat: {IMAGE_IN_FIGHT}")
    print(f"Zone principale surveillée: {OUT_FIGHT_REGION}")
    print(f"Zone combat: {IN_FIGHT_REGION}")
    print(f"Vérification toutes les {CHECK_INTERVAL} secondes")
    print(f"Délai entre clics: {CLICK_DELAY} secondes")
    print(f"Mode debug: {'Activé' if DEBUG_MODE else 'Désactivé'}")
    print("Appuyez sur Ctrl+C pour arrêter\n")
    
    # Configuration de pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.05
    
    # Chargement des images templates
    print("📷 Chargement des images templates..sss.")
    level_template = load_template_image(IMAGE_LEVEL)
    template = load_template_image(IMAGE_OUT_FIGHT)
    second_template = load_template_image(IMAGE_IN_FIGHT)
    join_template = load_template_image(IMAGE_JOIN)
    
    if level_template is None:
        print(f"❌ Impossible de charger l'image level up: {IMAGE_LEVEL}")
        return
    
    if template is None:
        print(f"❌ Impossible de charger l'image hors combat: {IMAGE_OUT_FIGHT}")
        return
    
    if second_template is None:
        print(f"❌ Impossible de charger l'image de combat: {IMAGE_IN_FIGHT}")
        return
    
    if join_template is None:
        print(f"❌ Impossible de charger l'image join: {IMAGE_JOIN}")
        return
    
    print("✅ Images templates chargées avec succès")
    
    # Créer l'overlay du compteur
    print("🖥️ Création de l'overlay du compteur...")
    create_counter_overlay()
    print("✅ Overlay du compteur créé")
    
    # Test de détection de l'image level up
    print("\n🧪 Exécution du test de détection level up...")
    test_level_up_detection(level_template)
    print("✅ Test terminé, début de la surveillance...\n")
    
    # Démarrage du thread de surveillance
    global watchdog_thread_ref
    watchdog_thread_ref = threading.Thread(target=watchdog_thread, daemon=True)
    watchdog_thread_ref.start()
    debug_print("Thread de surveillance démarré")
    
    # Reset du timer initial
    last_check_time = time.time()
    start_time = time.time()  # Initialiser le compteur de temps pour le restart
    
    try:
        while is_running:
            current_time = time.strftime('%H:%M:%S')
            print(f"\n🔍 Vérification à {current_time}...")
            
            # Mettre à jour l'interface du compteur
            if counter_window:
                counter_window.update()
            
            # Forcer un flush de stdout
            sys.stdout.flush()
            
            # 1. Vérifier d'abord si level up est présent
            level_detected = detect_image_in_region(level_template, LVL_REGION, "Level up", LVL_CONFIDENCE)
            if level_detected:
                perform_level_up_click()
                time.sleep(CHECK_INTERVAL)
                continue
            
            # 2. Sinon, vérifier si l'image hors combat est présente
            image_detected = detect_image_in_region(template, OUT_FIGHT_REGION, "Image hors combat")
            if image_detected:
                # Petit délai pour laisser le temps à l'interface de réagir
                time.sleep(2)

                # Exécuter les clics normaux
                perform_restart_dungeon()
                
                # Petit délai pour laisser le temps à l'interface de réagir
                time.sleep(1)
                
                # Vérifier si l'image join est présente après les clics
                join_detected = detect_image_in_region(join_template, JOIN_REGION, "Image join")
                
                if join_detected:
                    # L'image join est présente, effectuer le clic join
                    perform_join_click()
                    # Puis commencer la séquence de combat
                    perform_fight_sequence(second_template)
                else:
                    # Image join non détectée, continuer de surveiller jusqu'à ce qu'elle se présente
                    print("🔍 Image join non détectée, début de la surveillance continue...")
                    join_monitoring_start = time.time()
                    
                    while is_running:
                        # Vérifier si l'image join est présente
                        join_detected = detect_image_in_region(join_template, JOIN_REGION, "Image join (surveillance)")
                        
                        if join_detected:
                            print("🎉 Image join détectée pendant la surveillance !")
                            perform_join_click()
                            perform_fight_sequence(second_template)
                            break
                        else:
                            # Attendre un peu avant de revérifier
                            time.sleep(2)
                            
                            # Vérifier si on attend depuis trop longtemps (timeout de sécurité)
                            #if time.time() - join_monitoring_start > 60:  # 60 secondes de timeout
                                #print("⏰ Timeout de surveillance de l'image join, reprise normale")
                                #break
                
                # Pause courte avant de reprendre la surveillance principale
                time.sleep(1)
                continue
            
            # Aucune image détectée, attendre avant la prochaine vérification
            debug_print(f"Attente de {CHECK_INTERVAL}s...")
            for i in range(CHECK_INTERVAL):
                time.sleep(1)
                if DEBUG_MODE and i % 2 == 0:
                    print(".", end="", flush=True)
            
            if DEBUG_MODE:
                print()  # Nouvelle ligne après les points
            
    except KeyboardInterrupt:
        print("\n🛑 Script arrêté par l'utilisateur.")
        is_running = False
    except Exception as e:
        print(f"\n💥 Erreur inattendue: {e}")
        debug_print(f"Stack trace complet: {sys.exc_info()}")
        is_running = False
    finally:
        # Fermer l'overlay du compteur
        if counter_window:
            try:
                counter_window.window.destroy()
                counter_window.root.destroy()
                print("✅ Overlay du compteur fermé")
            except:
                pass

if __name__ == "__main__":
    main()