import pyautogui
import time
import msvcrt
import sys

print("Déplacez votre souris et appuyez sur Ctrl+C pour quitter")
print("Appuyez sur 's' pour sauvegarder une position")
print("Appuyez sur 's' une deuxième fois pour calculer la différence")

saved_positions = []

try:
    while True:
        x, y = pyautogui.position()
        print(f"Position: ({x}, {y})", end='\r')
        
        # Vérifier si une touche est pressée (non-bloquant)
        if msvcrt.kbhit():
            key = msvcrt.getch().decode('utf-8').lower()
            if key == 's':
                if len(saved_positions) == 0:
                    saved_positions.append((x, y))
                    print(f"\nPosition sauvegardée: ({x}, {y})")
                    print("Appuyez sur 's' une deuxième fois pour calculer la différence")
                elif len(saved_positions) == 1:
                    saved_positions.append((x, y))
                    pos1 = saved_positions[0]
                    pos2 = saved_positions[1]
                    
                    diff_x = abs(pos2[0] - pos1[0])
                    diff_y = abs(pos2[1] - pos1[1])
                    
                    print(f"\nPosition 1: ({pos1[0]}, {pos1[1]})")
                    print(f"Position 2: ({pos2[0]}, {pos2[1]})")
                    print(f"Différence: {diff_x}x{diff_y}")
                    
                    # Réinitialiser pour permettre de nouvelles mesures
                    saved_positions = []
                    print("Appuyez sur 's' pour une nouvelle mesure")
        
        time.sleep(0.1)
        
except KeyboardInterrupt:
    print(f"\nCoordonnées finales: ({x}, {y})")