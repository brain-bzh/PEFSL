"""
DEMO of few shot learning:
    connect to the camera and prints prediction in an interface
    press :
    1, 2, 3... : the program will register the current image as an instance of the given class
    i : will start inference
    q : quit the program
    p : pause the program
"""
print("Running...")
#'/usr/local/share/pynq-venv/lib/python3.8/site-packages', '', '', '/usr/lib/python3.8/dist-packages', '', '', '/home/xilinx'
import cv2
import numpy as np

from input_output.graphical_interface import OpencvInterface
from input_output.graphical_interface import Timer
from few_shot_model.few_shot_model import FewShotModel
from backbone_loader.backbone_loader import get_model
from few_shot_model.data_few_shot import DataFewShot
from args import get_args_demo
print("Imports done.")

def preprocess(img, dtype=np.float32):
    """
    Args : img(np.ndarray(h,w,c)) :
    """
    assert len(img.shape) == 3
    assert img.shape[-1] == 3

    if img.dtype != dtype:
        # not that this copy the image
        img = img.astype(dtype)
    img = img[None, :]
    mean = np.array([0.485, 0.456, 0.406], dtype=dtype)
    std = np.array([0.229, 0.224, 0.225], dtype=dtype)
    return (img / 255 - mean/std)

def get_gpio(overlay):
    from input_output.boutons_manager import ButtonsManager
    from pynq.lib import AxiGPIO
    btns_gpio_dict = overlay.ip_dict['btns_gpio']
    pynq_button = AxiGPIO(btns_gpio_dict).channel1 #GPIO1
    external_button = AxiGPIO(btns_gpio_dict).channel2 #GPIO2
    return (pynq_button, external_button)

def launch_demo(args):
    ####################################
    ###------# INITIALIZATION #------###
    ####################################
    RES_HDMI = (800, 600)  # width/height : https://urlz.fr/mFBP
    RES_OUTPUT = args.output_resolution
    FONT = cv2.FONT_HERSHEY_SIMPLEX
    GSCALE = args.general_scale # General scale (=1 for the pynq screen)

    # Fewshot model
    backbone = get_model(args.backbone_specs)
    few_shot_model = FewShotModel(args.classifier_specs)
    probabilities = None
    probas = None

    # Possible classes
    possible_input_keyboard = [chr(i+49) for i in range(4)] # maximum 4 class (you can replace the 4 by any positiv integer to increase nb_class_max)
    possible_input_pynq = ["1", "2", "3", "4"]
    nb_class_max = 0
    registered_class = None

    current_data = DataFewShot(nb_class_max) # useless parameters in DataFewShot (delete?)

    # State activation variable
    demo_ON = True
    current_state = "reset" # Always begin by a reset and then an initialization
    next_state = "reset"
    
    # Counter
    k_init = 0
    k_reg = 0

    # Time related variables 
    clock = 0 # number of frames since begining
    nb_frame_init = 5
    nb_features = 5 # number of frame saved as features for each shot of a class 

    # Keyboard/Buttons
    if args.button == "pynq":
        possible_input = possible_input_pynq
        nb_class_max = len(possible_input)
        pynq_button, external_button = get_gpio(args.overlay)
        from input_output.boutons_manager import ButtonsManager
        btn_manager = ButtonsManager(pynq_button, external_button, nb_class_max)
    elif args.button == "keyboard":
        possible_input = possible_input_keyboard
        nb_class_max = len(possible_input)
    elif args.button == "keyboard-pynq" or args.button == "sequence":
        possible_input = possible_input_pynq
        nb_class_max = len(possible_input)
        from input_output.boutons_manager import ButtonsManager
        btn_manager = ButtonsManager(None, None, nb_class_max)
    else:
        raise "Button argument invalid."
    
    # Terminal Interface
    T = Timer()
    # Camera
    cap = cv2.VideoCapture(args.camera_specification)
    cam_width_max = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    cam_height_max = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    cam_width, cam_height = args.camera_resolution
    if cam_width_max == 0 or cam_height_max == 0:
        raise "Can't find a camera."
    else:
        if cam_width > cam_width_max or cam_height > cam_height_max or cam_height/cam_width != 0.75:
            raise "Wrong camera resolution."
        else:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam_width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_height)
            cv_interface = OpencvInterface(cap, RES_OUTPUT,GSCALE, FONT, nb_class_max, args.max_fps)
    print("Camera resolution : ",int(cam_width),"x",int(cam_height))

    # Hdmi port
    if args.hdmi_display:
        from pynq.lib.video import VideoMode
        hdmi_out = args.overlay.video.hdmi_out
        mode = VideoMode(RES_HDMI[0], RES_HDMI[1], 24)  # 24 : pixel format
        hdmi_out.configure(mode)
        hdmi_out.start()
        new_frame = hdmi_out.newframe()
    
    ###############################
    ###------# MAIN LOOP #------###
    ###############################
    try:
        while True:
            T.tic(1) #initial time
            ###------# GET INPUTS #------###            
            ### KEYBOARD/BUTTON INPUT
            if args.button == "pynq":
                key = btn_manager.change_state()    
            elif args.button == "keyboard":
                key = cv_interface.get_key()
                key = chr(key)  # key convertion to char
            elif args.button == "keyboard-pynq":
                key = cv_interface.get_key()
                key = btn_manager.change_state2(key)
            elif args.button == "sequence" and (current_state=="idle" or current_state=="inference"):
                key = btn_manager.button_sequence()
            else:
                key = "0"
            T.toc("BUTTONS READ")

            if demo_ON:
                ### FRAME INPUT ###
                try:
                    cv_interface.read_frame()
                except:
                    print("failed to get next image")
                    exit(1)
                T.toc("FRAME READ")

                ############################
                ###------# STATES #------###
                ############################
                ### INITIALIZATION ###
                if current_state == "initialization":
                    # headband and text
                    cv_interface.draw_headband()
                    cv_interface.put_text("Initialization", 0.2)
                    # learn background during {nb_frame_init} frame
                    frame = cv_interface.resize_for_backbone(args.resolution_input)
                    frame = preprocess(frame)
                    T.tic()
                    features = backbone(frame)
                    T.toc("BACKBONE")
                    current_data.add_mean_repr(features)
                    if k_init >= nb_frame_init:
                        current_data.aggregate_mean_rep()
                        k_init = 0
                        next_state = "idle"
                    else:
                        next_state = "initialization"
                    k_init += 1
                    T.timer() # display all timers on the terminal

                ### REGISTRATION ###
                elif current_state == "registration":
                    # headband and text
                    cv_interface.draw_headband(1.75)
                    cv_interface.put_text(f"Class {classe} registered", 0.3)
                    cv_interface.put_text(f"Number of shots : {cv_interface.get_number_snapshot(classe)}", 0.315, 2)
                    # 10 (nb_features) following frames after pressing the button will be saved as features
                    frame = cv_interface.resize_for_backbone(args.resolution_input)
                    frame = preprocess(frame)
                    T.tic()
                    features = backbone(frame)
                    T.toc("BACKBONE")
                    current_data.add_repr(classe, features)
                    if k_reg >= nb_features:
                        next_state = "idle"
                        k_reg = 0
                    else:
                        next_state = "registration"
                    k_reg += 1
                    T.timer() # display all timers on the terminal

                ### INFERENCE ###
                elif current_state == "inference":
                    # do the inference
                    frame = cv_interface.resize_for_backbone(args.resolution_input)
                    frame = preprocess(frame)
                    T.tic()
                    features = backbone(frame)
                    T.toc("BACKBONE")
                    (classe_prediction, probabilities) = few_shot_model.predict_class_moving_avg(features, probabilities, current_data.get_shot_list(), current_data.get_mean_features())
                    T.toc("PREDI")
                    k = 0
                    for index in registered_class: # reorganize probabilities
                        probas[index] = probabilities[0,k]
                        k += 1
                    # headband, text and indicator
                    cv_interface.draw_headband()
                    T.tic()
                    cv_interface.put_text(f"Object is from class : {classe_prediction}", 0.38)
                    T.toc("TEXT")
                    cv_interface.draw_indicator(probas)
                    T.toc("INDICATORS")
                    T.timer() # display all timers on the terminal
                    next_state = "inference"

                ### PAUSE ###
                elif current_state == "pause":
                    # black screen and image
                    cv_interface.frame = np.zeros((RES_OUTPUT[1],RES_OUTPUT[0],3),dtype=np.uint8)
                    #image = cv2.imread("PEFSL/input_output/Logo_IMT_Atlantique.png")
                    #image = cv2.imread("/home/xilinx/Logo_IMT_Atlantique.png")
                    #cv_interface.display_image(image, 0.5)
                    clock = 0
                    demo_ON = False
                    T.ON = False

                ### IDLE ###
                elif current_state == "idle":
                    T.timer() # display all timers on the terminal
                    next_state = "idle"
                
                ### RESET ###
                elif current_state == "reset":
                    # reset states and values
                    current_data.reset()
                    cv_interface.reset_snapshot()
                    T.reset()
                    if args.button == "pynq" or args.button == "keyboard-pynq":
                        btn_manager.reset_button()
                    cv_interface.ERROR = False
                    cv_interface.empty_classe = []
                    probabilities = None
                    next_state = "initialization"
                    # headband and text
                    cv_interface.draw_headband()
                    cv_interface.put_text("Reset", 0.09)

                ### ERROR ###
                elif current_state == "error":
                    print("\r--- Class(es) ",f"{cv_interface.empty_classe} out of {nb_class} is/are empty. Please do a reset. ---",end="")
                    next_state = "error"

                else :
                    print("This state doesn't exist")
                    break

                ##########################################
                ###------# UPDATE CURRENT STATE #------###
                ##########################################
                
                ### CLASSES REGISTRATION ###
                if key in possible_input and not (current_state=="initialization" or current_state=="inference" or current_state=="registration"):
                    classe = possible_input.index(key)
                    cv_interface.add_snapshot(classe) # the first one will be saved for display
                    next_state = "registration"
                    
                ### INFERENCE ###
                elif key == "i" and current_data.is_data_recorded() and not (current_state=="inference"):
                    print("\n\n--- Beginning Inference ---")
                    T.saved_columns = T.columns.copy()
                    T.display = True
                    registered_class = sorted(list(map(int, current_data.registered_classes))) # transform list of string into list of int, and sort in ascending order
                    nb_class = registered_class[-1]+1
                    probas = nb_class*[0]
                    next_state = "inference"
                
                ### PAUSE ###
                elif key == "p":
                    # Pause the program
                    print("\n\n--- Turn off the demo ---")
                    next_state = "pause"
                
                ### RESET ###
                elif key == "r":
                    print("\n\n--- Reset ---")  
                    next_state = "reset"
                
                ### QUIT ###
                elif key == "q":
                    # Stop the program
                    print("\n\n--- Stopping... ---")
                    break

                ### ERROR ###
                elif cv_interface.ERROR:
                    print("\n")
                    cv_interface.ERROR = False
                    next_state = "error"
                
                current_state = next_state


                ###------# OUTPUTS #------###
                # Add fps and clock on frame
                clock += 1
                cv_interface.is_present_original_frame = False
                if not current_state=="pause":
                    T.tic()
                    cv_interface.put_fps_clock(np.round(1000*T.fps,1),clock)
                    T.toc("TEXT FPS CLOCK")
                T.toc("TOTAL TIME (ms)",1)
                T.fps_() # calculate fps
                T.columns["FPS"] = T.fps

                # Hdmi or computer screen
                if args.hdmi_display:
                    # get the frame from the cv interface (size is the same since they are specified by  ResOutput)
                    w, h = RES_OUTPUT
                    new_frame[:h, :w, :] = cv_interface.frame
                    T.toc("FRAME")
                    hdmi_out.writeframe(new_frame)
                    T.toc("WRITEFRAME")
                else:
                    cv_interface.show()
                

            else:
                if key == "p":
                    print("\n--- Turn on the demo ---")
                    demo_ON = True
                    T.ON = True
                    T.display = True
                    current_state = "reset"
                if key == 'q':
                    # Stop the program
                    print("\n\n--- Stopping ---")
                    break

    finally:
        # close all
        cv_interface.close()
        if args.hdmi_display:
            hdmi_out.close()


if __name__ == "__main__":
    args = get_args_demo()
    launch_demo(args)