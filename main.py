"""
DEMO of few shot learning:
    connect to the camera and prints prediction in an interface
    press :
    1, 2, 3... : the program will register the current image as an instance of the given class
    i : will start inference
    q : quit the program
"""


#'/usr/local/share/pynq-venv/lib/python3.8/site-packages', '', '', '/usr/lib/python3.8/dist-packages', '', '', '/home/xilinx'
import time
import cv2
import numpy as np
import os
import time

# import cProfile

from input_output.graphical_interface import OpencvInterface
from input_output.graphical_interface import OpencvInterface
from few_shot_model.few_shot_model import FewShotModel
from backbone_loader.backbone_loader import get_model
from few_shot_model.data_few_shot import DataFewShot
from args import get_args_demo

print("import done")


def compute_and_add_feature_saved_image(
    backbone, cv_interface, current_data, path_sample
):
    classe_idx = 0
    for class_name in os.listdir(path_sample):
        path_class = os.path.join(path_sample, class_name)

        for name_image in os.listdir(path_class):

            path_image = os.path.join(path_class, name_image)
            image = cv2.imread(path_image)
            image = cv2.resize(
                image, dsize=args.resolution_input, interpolation=cv2.INTER_LINEAR
            )
            cv_interface.add_snapshot(classe_idx, frame_to_add=image)
            image = preprocess(image)
            feature = backbone(image)
            current_data.add_repr(classe_idx, feature)
        classe_idx += 1


def preprocess(img, dtype=np.float32):
    """
    Args:
        img(np.ndarray(h,w,c)) :
    """
    assert len(img.shape) == 3
    assert img.shape[-1] == 3
    # img=img.astype(dtype)

    if img.dtype != dtype:
        # not that this copy the image
        img = img.astype(dtype)
    img = img[None, :]
    return (img / 255 - np.array([0.485, 0.456, 0.406], dtype=dtype)) / np.array(
        [0.229, 0.224, 0.225], dtype=dtype
    )


# constant of the program
SCALE = 1
#RES_OUTPUT = tuple(args.output_resolution) # weight / height (cv2 convention)
RES_HDMI= (600, 800) # weight height
#PADDING = tuple(args.padding)
FONT = cv2.FONT_HERSHEY_SIMPLEX


def launch_demo(args):
    """
    initialize the variable and launch the demo
    """

    # INITIALIZATION
    # --------------------------------------

    RES_OUTPUT= tuple(args.output_resolution)
    PADDING = tuple(args.padding)

    backbone = get_model(args.backbone_specs)
    few_shot_model = FewShotModel(args.classifier_specs)

    # data holding variables
    possible_input = [str(i) for i in range(177, 185)]
    possible_input_2 = ["1","2","3","4"]

    class_num = len(possible_input)
    current_data = DataFewShot(class_num)
    

    
    # program related constant
    do_inference = False
    doing_registration = False
    prev_frame_time = time.time()

    # time related variables
    # clock : number of frames since begining
    # clock_main : clock that control state of the program
    clock = 0
    clock_main = 0 
    number_frame_init = 5


    # CV2 related constant

    
    if not (args.camera_specification is None):
        cap = cv2.VideoCapture(args.camera_specification)

    # cv_interface manage graphical manipulation
    #TODO : add input/output to serparate class and use with statement
    cv_interface = OpencvInterface(cap, SCALE, RES_OUTPUT, FONT, class_num)
    
    if (args.hdmi_display):
        from pynq.lib.video import VideoMode
        hdmi_out = args.overlay.video.hdmi_out
        h,w = RES_HDMI
        mode = VideoMode(w, h, 24) # 24 : pixel format
        hdmi_out.configure(mode)
        hdmi_out.start()

    if args.button_keyboard == "button":
        from input_output.BoutonsManager import BoutonsManager
        btn_manager = BoutonsManager(args.overlay.btns_gpio)
    if args.save_video:
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        out = cv2.VideoWriter("output.avi", fourcc, 30.0, RES_OUTPUT)

    number_image = 1



    # MAIN LOOP
    # --------------------------------------
    try:
            

        while True:
            new_frame_time = time.time()
            fps = int(1 / (new_frame_time - prev_frame_time))

            # get inputs
            # video input
            try:
                cv_interface.read_frame()
                print(f"reading image n°{number_image}")
                print(f"fps : {fps}")
                number_image = number_image + 1
            except:
                print("failed to get next image")
                break

            prev_frame_time = new_frame_time

            # keyboard/button input
            if args.button_keyboard == "keyboard":
                key = cv_interface.get_key()
                key = chr(key)  # key convertion to char
            elif args.button_keyboard == "button":
                print("test_key_passage_avant")
                key = btn_manager.change_state()
                print("test_key_passage")
            elif args.button_keyboard == "button":
                key = btn_manager.change_state()
            else:
                print("L'argument button_keyboard n'est pas valide")

            # initialisation
            if clock_main <= number_frame_init:
                frame = cv_interface.get_copy_captured_image(args.resolution_input)
                frame = preprocess(frame)
                features = backbone(frame)

                current_data.add_mean_repr(features)
                if clock_main == number_frame_init:
                    current_data.aggregate_mean_rep()
                    if args.use_saved_sample:
                        path_sample = args.path_shots_video
                        compute_and_add_feature_saved_image(
                            backbone, cv_interface, current_data, path_sample
                        )
                        key = "i"  # simulate press of the key for inference

                        print(key)


                if key in possible_input or key in possible_input_2:
                    print("la key est bien dans les possibles inputs")
                    if key in possible_input :
                        classe = possible_input.index(key)
                    else :
                        classe = possible_input_2.index(key)
                    last_detected = clock_main * 1  # time.time()
                    



                cv_interface.put_text("Initialization")

            # if shot acquisition : stop inference and add image
            # once the key is pressed, the 10 following frames will be saved as snapshot
            # only the first one will be saved for display

            print("clock_main = ",clock_main, " nm frame init = ", number_frame_init)
            print("key in possible input : ", (key in possible_input_2))
            if (
                (key in possible_input or doing_registration or key in possible_input_2)

                and clock_main > number_frame_init
            ):
                do_inference = False
                

                if key in possible_input or key in possible_input_2:
                    print("la key est bien dans les possibles inputs")
                    if key in possible_input :
                        classe = possible_input.index(key)
                    else :
                        classe = possible_input_2.index(key)
                    last_detected = clock_main * 1  # time.time()
                    
                frame = cv_interface.get_copy_captured_image(args.resolution_input)
                
                print("la valeur de key avant le test des possibles inputs vaut : ", key )

                if ((key in possible_input) or (key in  possible_input_2)):

                    # if this is the first frame (ie there was an user input)
                    cv_interface.add_snapshot(classe)

                # add the representation to the class
                frame = preprocess(frame)
                features = backbone(frame)
                current_data.add_repr(classe, features)

                if abs(clock_main - last_detected) < 10:
                    doing_registration = True
                    text = f"Class :{classe} registered. \
                    Number of shots: {cv_interface.get_number_snapshot(classe)}"
                    cv_interface.put_text(text)
                else:
                    doing_registration = False

            # perform inference
            if do_inference and clock_main > number_frame_init:
                print("inference is running")
                frame = cv_interface.get_copy_captured_image(args.resolution_input)
                frame = preprocess(frame)
                features = backbone(frame)
                classe_prediction, probabilities = few_shot_model.predict_class_moving_avg(
                    features,
                    probabilities,
                    current_data.get_shot_list(),
                    current_data.get_mean_features(),
                )

                cv_interface.put_text(f"Object is from class :", classe_prediction)
                cv_interface.draw_indicator(probabilities)

                if args.no_display and not (args.save_video):

                    print("probabilities :", probabilities)

            # add info on frame
            cv_interface.put_text(f"fps:{fps}", bottom_pos_x=0.05, bottom_pos_y=0.1)
            cv_interface.put_text(
                f"frame number:{clock}", bottom_pos_x=0.8, bottom_pos_y=0.1
            )

            # update current state
            # reset action
            if key == "r":
                clock_main=0
                doing_registration = False
                do_inference = False
                current_data.reset()
                cv_interface.reset_snapshot()

            # inference action
            print("Valeur de key = ", key, " Valeur de current data.isrecorded = ", current_data.is_data_recorded())
            
            # Dans la ligne suivante, il faudra enlever le not, je l'ai ajouté pour faire l'inférence
            if key == "i" and current_data.is_data_recorded():
                print("Begining Inference")
                do_inference = True
                probabilities = None 

            # quit action
            if key == "q" or (
                not (args.max_number_of_frame is None)
                and number_image > args.max_number_of_frame
            ):
                # stop simulation if max number of frame is attained
                print("stoping simu")
                break

            clock_main += 1
            clock+=1

            # outputs
            print("no display", args.no_display)
            if not (args.no_display):

                if (args.hdmi_display):
                    # Returns a frame of the appropriate size for the video mode (undefined value)
                    frame = hdmi_out.newframe() 
                    # get the frame from the cv interface (size is the same since they are specified by  ResOutput)
                    
                    w,h=RES_OUTPUT
                    pw,ph=PADDING
                    frame[ph:ph+h,pw:pw+w,:] =  cv_interface.frame

                    hdmi_out.writeframe(frame)
                else:
                    cv_interface.show()

            
            if args.save_video:
                frame_to_save = cv_interface.frame
                out.write(frame_to_save)
    finally:
        # close all
        cv_interface.close()
        #hdmi_out.close()
        if args.save_video:
            out.release()
    


if __name__=="__main__":
    args=get_args_demo()
    launch_demo(args)
    