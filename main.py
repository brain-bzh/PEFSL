"""
DEMO of few shot learning:
    connect to the camera and prints prediction in an interface
    press :
    1, 2, 3... : the program will register the current image as an instance of the given class
    i : will start inference
    q : quit the program
"""


#'/usr/local/share/pynq-venv/lib/python3.8/site-packages', '', '', '/usr/lib/python3.8/dist-packages', '', '', '/home/xilinx'
import cv2
import numpy as np
import os
import time
from typing import Union
import sys
# import cProfile

from input_output.graphical_interface import OpencvInterface
from input_output.graphical_interface import OpencvInterface
from few_shot_model.few_shot_model import FewShotModel
from backbone_loader.backbone_loader import get_model
from few_shot_model.data_few_shot import DataFewShot
from args import get_args_demo

print("import done")

def custom_format(value):
    width = 7
    return"{: >{width}.2f}".format(value, width=width)

class Terminal:
    def __init__(self, period=0.5):
        self.flag_log = False
        self.time = time.time()
        self.period = period
    def log(self, fps, total_time, frameread_time, backbone_time, probabilities):
        if not self.flag_log:
            self.flag_log = True
            print("   FPS    | TOTAL TIME (ms) | FRAME READ TIME (ms) | BACKBONE TIME (ms) |")
        if(time.time() - self.time > self.period):
            self.time = time.time()
            print('\r' + custom_format(fps), end='')
            print("   |       ", end="")
            print(custom_format(total_time*1000), end='')
            print("   |            ", end="")
            print(custom_format(frameread_time*1000), end='')
            print("   |          ", end="")
            if (backbone_time is not None):
                print(custom_format(backbone_time*1000), end='')
            else:
                print("    N/A", end='')
            print("   | ", end="")
            if probabilities is not None:
                print("PROBABILITIES: ", end="")
                for data in probabilities.flatten():
                    print("{:>4.2f} %, ".format(data*100), end='')
                sys.stdout.write("\b")
                sys.stdout.write("\b")
                sys.stdout.write(" ")
                sys.stdout.write(" ")
        sys.stdout.flush()


def compute_and_add_feature_saved_image(
    backbone,
    cv_interface: OpencvInterface,
    current_data,
    path_sample: Union[str, os.PathLike],
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

# RES_OUTPUT = tuple(args.output_resolution) # weight / height (cv2 convention)
RES_HDMI = (600, 800)  # weight height
# PADDING = tuple(args.padding)
FONT = cv2.FONT_HERSHEY_SIMPLEX


def launch_demo(args):
    """
    initialize the variable and launch the demo
    """

    # INITIALIZATION
    # --------------------------------------

    RES_OUTPUT = tuple(map(int,args.output_resolution.split('x')))
    
    FONT_SCALE = 0.001*RES_OUTPUT[0]
    FONT_THICKNESS = int(np.round(0.0025*RES_OUTPUT[0]))
    PADDING = tuple(args.padding)
    if FONT_THICKNESS==0:
        FONT_THICKNESS = 1

    backbone = get_model(args.backbone_specs)
    few_shot_model = FewShotModel(args.classifier_specs)

    # data holding variables
    possible_input_keyboard = [chr(i) for i in range(177, 185)]
    possible_input_pynq = ["1", "2", "3", "4"]

    class_num = len(possible_input_keyboard)
    current_data = DataFewShot(class_num)

    # program related constant
    do_inference = False
    doing_registration = False
    do_reset = False

    # time related variables
    # clock : number of frames since begining
    # clock_main : clock that control state of the program
    clock = 0
    clock_main = 0
    number_frame_init = 5
    number_frame_restart = 5

    terminal = Terminal()

    # CV2 related constant

    if not (args.camera_specification is None):
        cap = cv2.VideoCapture(args.camera_specification)
        # cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    # cv_interface manage graphical manipulation
    # TODO : add input/output to serparate class and use with statement
    cv_interface = OpencvInterface(cap, RES_OUTPUT, FONT, FONT_SCALE, FONT_THICKNESS, class_num)

    if args.hdmi_display:
        from pynq.lib.video import VideoMode
        hdmi_out = args.overlay.video.hdmi_out
        h, w = RES_HDMI
        mode = VideoMode(w, h, 24)  # 24 : pixel format
        hdmi_out.configure(mode)
        hdmi_out.start()
    
    if args.button_keyboard == "button":
        from input_output.boutons_manager import BoutonsManager
        from pynq.lib import AxiGPIO

        axi_gpio_design = args.overlay
        btns_gpio_dict = axi_gpio_design.ip_dict['btns_gpio']

        local_button = AxiGPIO(btns_gpio_dict).channel1 #GPIO
        external_button = AxiGPIO(btns_gpio_dict).channel2 #GPIO2

        btn_manager = BoutonsManager(local_button, external_button)
    
    if args.save_video:
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        out = cv2.VideoWriter("output.avi", fourcc, 30.0, RES_OUTPUT)

    number_image = 1
    fps = 0

    # MAIN LOOP
    # --------------------------------------
    try:
        while True:

            # get inputs
            # video input
            initial_time = time.time()
            backbone_time = None
            probabilities = None
            try:
                cv_interface.read_frame()
                number_image = number_image + 1
            except:
                print("failed to get next image")
                exit(1)
            frameread_time = time.time() - initial_time
            
            # keyboard/button input
            if args.button_keyboard == "keyboard":
                key = cv_interface.get_key()
                key = chr(key)  # key convertion to char
                possible_input = possible_input_keyboard
            elif args.button_keyboard == "button":
                key = btn_manager.change_state()
                possible_input = possible_input_pynq
            else:
                print("Arg button_keyboard invalid")
            
            # initialization
            if clock_main <= number_frame_init:
                frame = cv_interface.get_copy_captured_image(args.resolution_input)
                frame = preprocess(frame)

                pre_backbone_time = time.time()
                features = backbone(frame)
                backbone_time = (time.time() - pre_backbone_time)
                current_data.add_mean_repr(features)
                if clock_main == number_frame_init:
                    current_data.aggregate_mean_rep()
                    if args.use_saved_sample:
                        path_sample = args.path_shots_video
                        compute_and_add_feature_saved_image(backbone, cv_interface, current_data, path_sample)
                        key = "i"  # simulate press of the key for inference

                        print(key)

                if key in possible_input:
                    classe = possible_input.index(key)
                    last_detected = clock_main * 1  # time.time()
                
                cv_interface.draw_headband()
                cv_interface.put_text("Initialization", 0.2)

            # if shot acquisition : stop inference and add image
            # once the key is pressed, the 10 following frames will be saved as snapshot
            # only the first one will be saved for display
            if (
                (key in possible_input or doing_registration)
                and clock_main > number_frame_init
                and not do_reset
            ):
                do_inference = False

                if key in possible_input:
                    classe = possible_input.index(key)
                    last_detected = clock_main * 1  # time.time()

                frame = cv_interface.get_copy_captured_image(args.resolution_input)

                if key in possible_input:
                    # if this is the first frame (ie there was an user input)
                    cv_interface.add_snapshot(classe)

                # add the representation to the class
                frame = preprocess(frame)

                pre_backbone_time = time.time()
                features = backbone(frame)
                backbone_time = (time.time() - pre_backbone_time)
                current_data.add_repr(classe, features)

                if abs(clock_main - last_detected) < 10:
                    doing_registration = True
                    cv_interface.draw_headband(1.75)
                    cv_interface.put_text(f"Class : {classe} registered", 0.3)
                    cv_interface.put_text(f"Number of shots : {cv_interface.get_number_snapshot(classe)}", 0.315, 2)
                    if(clock_main - last_detected == 0):
                        print(f"Class : {classe} registered. Number of shots : {cv_interface.get_number_snapshot(classe)}")
                else:
                    doing_registration = False

            # perform inference
            if do_inference and clock_main > number_frame_init and not do_reset:
                frame = cv_interface.get_copy_captured_image(args.resolution_input)
                frame = preprocess(frame)

                pre_backbone_time = time.time()
                features = backbone(frame)
                backbone_time = (time.time() - pre_backbone_time)

                (
                    classe_prediction,
                    probabilities,
                ) = few_shot_model.predict_class_moving_avg(
                    features,
                    probabilities,
                    current_data.get_shot_list(),
                    current_data.get_mean_features(),
                )
                cv_interface.draw_headband()
                cv_interface.put_text(f"Object is from class : {classe_prediction}", 0.38)
                cv_interface.draw_indicator(probabilities)

            # add fps and clock on frame
            cv_interface.put_fps_clock(fps,clock)

            # update current state
            # reset action
            if key == "r":
                clock_main = 0
                doing_registration = False
                do_inference = False
                current_data.reset()
                cv_interface.reset_snapshot()
                do_reset = True

            if do_reset == True and clock_main > number_frame_restart:
                do_reset = False
                #cv_interface.draw_headband()
                #cv_interface.put_text("Reset", 0.09)
            
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
                print("Stopping...")
                break
            
            clock_main += 1
            clock += 1

            # outputs
            if not (args.no_display):
                if args.hdmi_display:
                    # Returns a frame of the appropriate size for the video mode (undefined value)
                    frame = hdmi_out.newframe()
                    # get the frame from the cv interface (size is the same since they are specified by  ResOutput)

                    w, h = RES_OUTPUT
                    pw, ph = PADDING
                    frame[ph : ph + h, pw : pw + w, :] = cv_interface.frame

                    hdmi_out.writeframe(frame)
                else:
                    cv_interface.show()

            if args.save_video:
                frame_to_save = cv_interface.frame
                out.write(frame_to_save)
            total_time = time.time() - initial_time
            fps = np.round(1 / (total_time),1)

            terminal.log(fps, total_time, frameread_time, backbone_time, probabilities)

    finally:
        # close all
        cv_interface.close()
        if args.hdmi_display:
            hdmi_out.close()
        if args.save_video:
            out.release()


if __name__ == "__main__":
    args = get_args_demo()
    launch_demo(args)
