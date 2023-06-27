"""
manage the graphical interface and camera for the demo
"""
import cv2
import numpy as np


def draw_indic2(frame, percentages, shot_frames, font, font_scale, font_thickness):
    def percentage_to_color(p):
        return 0,255 - (255 * p), 255 * p
    
    percentages = percentages[0]  # not clean,

    ###PARAMETERS###
    #general
    height, width, _ = frame.shape
    bloc_gap = int(0.04 * height)
    #headband
    headband_height = int(0.1*height)
    #shot_frames
    shot_width = int(0.2*width)
    shot_height = int(0.2*height)
    shot_shift = int(0.01*width)
    shot_gap = int(0.02*height)
    #level bar
    level_bar_width = int(0.02*width)
    level_bar_height = shot_height
    #percentage
    font_percentage_scale = font_scale
    font_class_scale = 0.7*font_percentage_scale
    font_percentage_thickness = font_thickness
    font_class_thickness = int(0.7*font_percentage_thickness)
    if font_thickness==0:
        font_percentage_thickness = 1
        font_class_thickness = 1


    ###DRAW SHOT WITH SHIFT###
    #init position of the first shot
    x_start = bloc_gap + shot_gap
    x_end = bloc_gap + shot_gap + shot_width
    y_start = headband_height + bloc_gap + shot_gap
    y_end = headband_height + bloc_gap + shot_gap + shot_height

    for k in range (percentages.shape[0]):
        images = shot_frames[k]
        if y_end<height:
            #draw shots
            for n_shot in range(len(images)):
                frame[y_start:y_end , x_start:x_end] = images[n_shot]
                x_start = x_start + shot_shift
                x_end = x_end + shot_shift
                y_start = y_start + shot_shift
                y_end = y_end + shot_shift
            cv2.putText(frame,f"class {k}",(x_start, y_end - shot_height + 2*shot_shift),font,font_class_scale,(0, 0, 255),font_class_thickness,cv2.LINE_AA)
            cv2.putText(frame,f"{n_shot+1}",(x_end - 4*shot_shift, y_end - shot_height + 2*shot_shift),font,font_class_scale,(0, 0, 255),font_class_thickness,cv2.LINE_AA)
            #draw level
            x_start = x_end - shot_shift + shot_gap
            y_start = y_end - shot_shift
            level_max = int(percentages[k] * level_bar_height)
            for lvl in range(level_max):
                level_start = (x_start , y_start - lvl)
                level_end = (x_start + level_bar_width , y_start - (lvl+1))
                cv2.rectangle(frame,level_start,level_end,percentage_to_color(lvl/level_bar_height),cv2.FILLED)
            #draw percentage
            x_start = x_start + shot_gap + level_bar_width
            y_start = y_start
            percentage_origin = (x_start , y_start)
            cv2.putText(frame,f"{int(100*percentages[k].item())}%",percentage_origin,font,font_percentage_scale,(0, 0, 255),font_percentage_thickness,cv2.LINE_AA)
            #update position for the next class
            x_start = bloc_gap + shot_gap
            x_end = x_start + shot_width
            y_start = y_start + shot_gap
            y_end = y_start + shot_height


def draw_indic(frame, percentages, shot_frames, font, font_scale):
    """
    Args :
        percentages : (np.ndarray(1,n_features) ) : probability of belonging to each class
    """
    percentages = percentages[0]  # not clean,

    def percentage_to_color(p):
        return 0, 255 - (255 * p), 255 * p

    height, width, _ = frame.shape
    # config
    levels = 50
    level_width = width // 10
    level_height = 5
    shift_y = int(height * 0.4)
    # draw

    cv2.rectangle(
        frame,
        (20, shift_y - level_height * (levels + 10)),
        (
            20 + level_width * (percentages.shape[0] - 1) + level_width - 10,
            shift_y - level_height * (levels + 1),
        ),
        (0, 0, 0),
        cv2.FILLED,
    )
    cv2.rectangle(
        frame,
        (20, shift_y + level_height * 1),
        (
            20 + level_width * (percentages.shape[0] - 1) + level_width - 10,
            shift_y + level_height * 10,
        ),
        (0, 0, 0),
        cv2.FILLED,
    )
    for k in range(percentages.shape[0]):
        images = shot_frames[k]
        s = images[0].shape
        y_start_img = shift_y
        x_start_img = 15 + level_width * k
        for n_shot in range(len(images)):
            if y_start_img + s[0] + n_shot * (s[0] + 10) < frame.shape[0]:
                frame[
                    y_start_img
                    + n_shot * (s[0] + 10) : y_start_img
                    + s[0]
                    + n_shot * (s[0] + 10),
                    x_start_img : x_start_img + s[1],
                ] = images[n_shot]
        img_level = int(percentages[k] * levels)
        cv2.putText(
            frame,
            f"{np.round(100*percentages[k].item(), 2)}%",
            (20 + level_width * k, shift_y - level_height * (levels + 3)),
            font,
            font_scale,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

        cv2.rectangle(
            frame,
            (20 + level_width * k, shift_y - levels * level_height),
            (20 + level_width * k + level_width - 10, shift_y),
            (0, 0, 0),
            cv2.FILLED,
        )
        for i in range(img_level):
            level_y_b = shift_y - i * level_height
            start_point = (20 + level_width * k, level_y_b - level_height)
            end_point = (20 + level_width * k + level_width - 10, level_y_b)
            cv2.rectangle(
                frame,
                start_point,
                end_point,
                percentage_to_color(i / levels),
                cv2.FILLED,
            )


class OpencvInterface:
    """
    Class representing the opencv configuration
    (Manage the camera and the graphical interface)
    this class also has the frame attribute since it needs ownership (to modify it)
    once the image is modified, you can no longer access it
    ...

    Attributes :
        video_capture(cv.VideoCapture) : camera used
        height : height of the interface
        width : width of the interface
        resolution : height, width of the interface
        font : font used by opencv
        font_scale : scale of the font
        font_thickness : thickness of the font
        frame : current captured frame
        number_of_class : number of possible class
        snapshot : saved snapshots
        is_available_frame : weither the frame is available for capture


    """

    def __init__(self, video_capture, resolution, font, font_scale, font_thickness, number_of_class):
        self.video_capture = video_capture
        self.font = font
        self.font_scale = font_scale
        self.font_thickness = font_thickness
        self.height = resolution[0]
        self.width = resolution[1]
        self.resolution = resolution
        self.font = font
        self.frame = None
        self.number_of_class = number_of_class
        self.snapshot = [[] for i in range(number_of_class)]
        self.is_present_original_frame = False

    def read_frame(self):
        """
        read and resize the frame to interface size
        """
        _, frame = self.video_capture.read()
        self.frame = cv2.resize(frame, self.resolution, interpolation=cv2.INTER_AREA)
        self.is_present_original_frame = True

    def get_copy_captured_image(self, resolution):
        """
        return a resized copy of the captured image if it still present in the data
        """

        if self.is_present_original_frame:
            return cv2.resize(
                self.frame, dsize=resolution, interpolation=cv2.INTER_LINEAR
            )  # linear is faster than cubic
        else:
            raise Exception("original frame is not available")
    
    def draw_indicator(self, probabilities):
        """
        wrapper of draw_indic
        """
        self.is_present_original_frame = False
        #draw_indic(self.frame, probabilities, self.snapshot, self.font, self.font_scale)
        draw_indic2(self.frame, probabilities, self.snapshot, self.font, self.font_scale, self.font_thickness)

    def draw_headband(self, under_band = 1):
        """
        parameters :
            under_band (float) : permit to draw a band under the headband : 1 (default) : draw the headband / 1.75 : draw the headband & an underband
        """      
        self.is_present_original_frame = False
        
        height, width, _ = self.frame.shape

        ###HEADBAND###
        headband_width = width
        headband_height = int(under_band*0.1*height)
        cv2.rectangle(self.frame,(0,headband_height),(headband_width,0),(255,255,255),cv2.FILLED)

    def put_text(self, text, length_proportion, level = 1):
        """
        put some text in the interface
            parameters :
                text(string) : text to be added
                length_proportion (0<float<1): proportion of the length of the text relative to the frame, used to center the text
                level (int) : text writing level : 1 (default) : in the headband / 2 : in the underband 
        """
        self.is_present_original_frame = False

        height, width, _ = self.frame.shape

        headband_height = int(0.1*height)
        top_gap = int(0.74*headband_height)
        length = int(length_proportion*width)
        origin = (width//2 - length//2 , level*top_gap)
        cv2.putText(self.frame, text, origin, self.font, self.font_scale, (0, 0, 255), self.font_thickness, cv2.LINE_AA)   

    def put_fps_clock(self, fps, clock):
        """
        write fps on the left and clock on the right of the headband
        """

        height, width, _ = self.frame.shape

        headband_width = width
        headband_height = int(0.1*height)
        top_gap = int(0.74*headband_height)
        bloc_gap = int(0.04 * height)

        #put fps on the frame
        cv2.putText(self.frame, f'fps : {fps}', (bloc_gap , top_gap), self.font, self.font_scale, (0, 0, 0), self.font_thickness, cv2.LINE_AA)
    
        #calculate the shift to shift the clock for every decade
        div = clock
        clock_shift_text = 0
        while div>=10:
            div = div/10
            clock_shift_text += 1

        #draw white rectangle to see the fps
        fps_start = (0 , headband_height)
        fps_end = (bloc_gap + int(0.18*width), 0)
        cv2.rectangle(self.frame, fps_start, fps_end, (255,255,255), cv2.FILLED)
        #draw white rectangle to see the clock
        clock_origin = (width - bloc_gap - int(0.15*width) - clock_shift_text*int(0.019*width) , top_gap)
        clock_start = (clock_origin[0] - bloc_gap , headband_height)
        clock_end = (width , 0)
        cv2.rectangle(self.frame, clock_start, clock_end, (255,255,255), cv2.FILLED)

        #put clock on the frame
        cv2.putText(self.frame, f'clock : {clock}', clock_origin, self.font, self.font_scale, (0, 0, 0), self.font_thickness, cv2.LINE_AA)

    def show(self):
        """
        show the current updated frame
        """
        cv2.imshow("frame", self.frame)

    def add_snapshot(self, classe, frame_to_add=None):
        """
        add a snapshot to memmory
        """
        if frame_to_add is None:
            frame_to_add = self.frame
        image_label = cv2.resize(
            frame_to_add,
            (int(0.2*self.height), int(0.2*self.width)),
            interpolation=cv2.INTER_AREA,
        )
        self.snapshot[classe].append(image_label)

    def get_number_snapshot(self, classe):
        """
        get the number of snapshot of a given classe"""
        return len(self.snapshot[classe])

    def reset_snapshot(self):
        """
        reset the snapshot to initial value"""
        self.snapshot = [[] for i in range(self.number_of_class)]

    def close(self):
        """
        liberate all attributed ressources
        """
        self.video_capture.release()
        cv2.destroyAllWindows()

    def get_key(self):
        """
        if a key was pressed, get the key
        """
        return cv2.waitKey(33) & 0xFF
