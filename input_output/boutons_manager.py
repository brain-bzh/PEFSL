class BoutonsManager:
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

    def __init__(self, local_button, external_button):
        """
        button gpio : btns_gpio attribute of the overlay
        see : https://pynq.readthedocs.io/en/v2.0/pynq_libraries/axigpio.html
        """
        self.local_button = local_button
        self.external_button = external_button
        self.key_pressed = "1"
        self.last_state = 0

    def change_state(self):
        
        local = self.local_button.read()
        external = self.external_button.read()
        if external==31: # in case of no pin are connected
            external = 0

        state = local | external

        if state != self.last_state:
            if state != 0:
                if state == 1:
                    # prendre une image
                    if self.key_pressed == "r":
                        self.key_pressed = "1"
                    self.last_state = state
                    return self.key_pressed

                if state == 2:
                    # changer de classe
                    self.key_pressed = str(int(self.key_pressed) + 1)
                    print("Now registering class: " + self.key_pressed)
                    self.last_state = state
                    return self.key_pressed

                if state == 4:
                    # faire l'inference
                    self.key_pressed = "i"
                    self.last_state = state
                    return self.key_pressed

                if state == 8:
                    # reset
                    self.key_pressed = "r"
                    print("Now registering class 1")
                    self.last_state = state
                    return self.key_pressed
                
                if state == 16:
                    #on/off
                    self.key_pressed = "b"
                    self.last_state = state
                    return self.key_pressed

            self.last_state = state
        return "NO_KEY_PRESSED"


if __name__ == "__main__":
    # test the bouton
    import time
    import numpy as np
    import pynq
    from pynq import Overlay
    from tcu_pynq.driver import Driver
    from tcu_pynq.architecture import pynqz1
    import sys  # TODO : à supprimer

    sys.path.append("/home/xilinx")

    overlay = Overlay("/home/xilinx/jupyter_notebooks/l20leche/base_tensil_hdmi.bit")
    btns = BoutonsManager(overlay.btns_gpio)
    while True:
        time.sleep(1)
        print(btns.change_state())
