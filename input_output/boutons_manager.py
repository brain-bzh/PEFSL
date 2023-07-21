import time

class ButtonsManager:
    """
    La classe boutons renvoie grâce à la méthode change_state, la touche du clavier qui aurait
    été tappée si au lieu des boutons nous avions utiliser un clavier.
    Lorsque l'on appuie sur le bouton 1 pour capturer une image, change_state renvoie le numéro de
    la classe à laquelle appartient l'image. Lorsqu'on appuie sur le bouton 2, il y a un changement
    de classe et change_state renvoie toujours le numéro de la classe à laquelle appartient l'image.
    Lorsqu'on appuie sur le bouton 3, change_state renvoie "i" pour indiquer qu'il faut passer à l'inférence
    Lorsqu'on appuie sur le bouton 4, change_state renvoie "r" pour indiquer un reset
    Si aucun pouton n'a été pressé, change_state renvoie "NO_KEY_PRESSED"
    """

    def __init__(self, pynq_button, external_button, nb_class_max):
        """
        button gpio : btns_gpio attribute of the overlay
        see : https://pynq.readthedocs.io/en/v2.0/pynq_libraries/axigpio.html
        """
        self.pynq_button = pynq_button
        self.external_button = external_button
        self.nb_class_max = nb_class_max
        self.last_state = 0
        self.last_class = 0
        self.reach_max = False
        self.key_pressed = "1"
        self.nb_class = 0
        self.nb_shot = 0
        self.wait = time.time()
        self.start = time.time()

    def change_state(self):
        
        pynq = self.pynq_button.read()
        external = self.external_button.read()
        if external==31:
            external = 0

        state = pynq | external

        if state != self.last_state:
            if state != 0:
                if state == 1:
                    # take a shot of the current class
                    self.last_state = state
                    return self.key_pressed

                if state == 2:
                    # change class
                    if int(self.key_pressed) >= self.nb_class_max:
                        print(" Maximum class reached.")
                        self.reach_max = True
                    else:
                        print(" Now registering class " + self.key_pressed + ".", end='')
                        self.key_pressed = str(int(self.key_pressed) + 1)
                    self.last_state = state
                    return self.key_pressed

                if state == 4:
                    # do inference
                    self.key_pressed = "i"
                    self.last_state = state
                    return self.key_pressed

                if state == 8:
                    # reset
                    self.key_pressed = "r"
                    self.last_state = state
                    return self.key_pressed
                
                if state == 16:
                    # pause (on/off)
                    self.key_pressed = "p"
                    self.last_state = state
                    return self.key_pressed
                
                if state == 32:
                    # quit
                    self.key_pressed = "q"
                    self.last_state = state
                    return self.key_pressed

            self.last_state = state

        return "NO_KEY_PRESSED"
    
    def change_state2(self,key):
        
        if key==255:
            key = 0
        elif key==176:
            key = 1
        elif key==177:
            key = 2
        elif key==178:
            key = 4
        elif key==179:
            key = 8
        elif key==180:
            key = 16
        elif key==113:
            key = 32
        else:
            key = 0
        state = key

        if state != self.last_state:
            if state != 0:
                if state == 1:
                    # take a shot of the current class
                    self.last_state = state
                    return self.key_pressed

                if state == 2:
                    # change class
                    if int(self.key_pressed) >= self.nb_class_max:
                        print(" Maximum class reached.")
                        self.reach_max = True
                    else:
                        print(" Now registering class " + self.key_pressed + ".", end='')
                        self.key_pressed = str(int(self.key_pressed) + 1)
                    self.last_state = state
                    return self.key_pressed

                if state == 4:
                    # do inference
                    self.key_pressed = "i"
                    self.last_state = state
                    return self.key_pressed

                if state == 8:
                    # reset
                    self.key_pressed = "r"
                    self.last_state = state
                    return self.key_pressed
                
                if state == 16:
                    # pause (on/off)
                    self.key_pressed = "p"
                    self.last_state = state
                    return self.key_pressed
                
                if state == 32:
                    # quit
                    self.key_pressed = "q"
                    self.last_state = state
                    return self.key_pressed

            self.last_state = state

        return "NO_KEY_PRESSED"
    

    def button_sequence(self, period=1, timeout=15):
        if(time.time() - self.start < timeout):
            if(time.time() - self.wait > period):
                self.wait = time.time()
                if self.nb_class < 2:
                    if self.nb_shot < 2:
                        self.nb_shot += 1
                        return self.key_pressed
                    else:
                        self.nb_shot = 0
                        self.nb_class += 1
                        if self.nb_class < 2:
                            self.key_pressed = str(int(self.key_pressed) + 1)
                            return self.key_pressed            
                else:
                    self.key_pressed = "i"
                    return self.key_pressed
            return "0"
        else:
            return "q"
                
        

    def reset_button(self):
        self.key_pressed = "1"
        self.last_state = 0
        self.reach_max = False