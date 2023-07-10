"""
manage the graphical interface and camera for the demo
"""
import cv2
import numpy as np
import time

def percentage_to_color(p):
    return 0,255 - (255 * p), 255 * p

def display_img(frame, image, scale, position="ctr/ctr"):
    """
    Args :
        frame : frame where display the image
        image : image to display
        scale (0<_<1): scale compared to the frame (1=same size as the frame / 0.5=half the frame)
        position "pos1/pos2": top, btm, ctr, rgt, lft
    """
    HEIGHT, WIDTH, _ = frame.shape
    height = int(scale*HEIGHT)
    width = int(scale*WIDTH)
    image = cv2.resize(image, (width, height), interpolation=cv2.INTER_LINEAR)

    image_shift = int(0.05*WIDTH)
    pos1, pos2 = tuple(map(str,position.split('/')))

    if pos1=="top":
        y_start = image_shift
        if pos2=="lft":
            x_start = image_shift
        if pos2=="ctr":
            x_start = WIDTH//2 - width//2
        if pos2=="rgt":
            x_start = WIDTH - image_shift - width
    if pos1=="ctr":
        y_start = HEIGHT//2 - height//2
        if pos2=="lft":
            x_start = image_shift
        if pos2=="ctr":
            x_start = WIDTH//2 - width//2
        if pos2=="rgt":
            x_start = WIDTH - image_shift - width
    if pos1=="btm":
        y_start = HEIGHT-image_shift
        if pos2=="lft":
            x_start = image_shift
        if pos2=="ctr":
            x_start = WIDTH//2 - width//2
        if pos2=="rgt":
            x_start = WIDTH - image_shift - width

    x_end = x_start + width
    y_end = y_start + height  
    
    frame[y_start:y_end, x_start:x_end] = image


class OpencvInterface:
    """
    Class representing the opencv configuration
    (Manage the camera and the graphical interface)
    this class also has the frame attribute since it needs ownership (to modify it)
    once the image is modified, you can no longer access it
    ...

    Attributes :
        video_capture(cv.VideoCapture) : camera used
        resolution : height, width of the interface
        height : height of the interface
        width : width of the interface
        Gscale : general scale of the interface (=1 on the pynq)
        font : font used by opencv
        font_scale : scale of the font
        font_thickness : thickness of the font
        headband_height : height of the headband
        top_gap : height for the text in the headband
        bloc_gap : gap between each component of the interface
        shot_heigth : height of shots to display
        shot_width : width of shots to display
        frame : current captured frame
        number_of_class : number of possible class
        snapshot : saved snapshots


    """

    def __init__(self, video_capture, resolution, Gscale, font, number_of_class):
        self.video_capture = video_capture
        self.resolution = resolution
        self.height = resolution[1]
        self.width = resolution[0]
        self.Gscale = Gscale
        self.font = font
        self.font_scale = Gscale*0.001*self.width
        self.font_thickness = int(np.round(Gscale*0.0025*self.width))
        self.headband_height = int(Gscale*0.1*self.height)
        self.top_gap = int(0.67*self.headband_height)
        self.bloc_gap = int(Gscale*0.04*self.height)
        self.shot_height = int(Gscale*0.2*self.height)
        self.shot_width = int(Gscale*0.2*self.width)
        self.frame = None
        self.number_of_class = number_of_class
        self.snapshot = [[] for i in range(number_of_class)]
        self.ERROR = False
        self.empty_classe = []
        
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
            return cv2.resize(self.frame, dsize=resolution, interpolation=cv2.INTER_LINEAR)  # linear is faster than cubic
        else:
            raise Exception("original frame is not available")
    
    def display_image(self, image, scale, position="ctr/ctr"):
        """
        wrapper of display_img
        """
        display_img(self.frame, image, scale, position)


    def draw_indicator(self, probabilities):
        """
        Draw indicator : draw shots, probability and level bar for each class
        """

        ###PARAMETERS###
        #shot_frames
        shot_width = self.shot_width
        shot_height = self.shot_height
        shot_shift = int(self.Gscale*0.01*self.width)
        shot_gap = int(self.Gscale*0.025*self.height)
        #level bar
        level_bar_width = int(0.02*self.width)
        level_bar_height = shot_height
        #percentage
        font_percentage_scale = self.font_scale
        font_class_scale = 0.7*font_percentage_scale
        font_percentage_thickness = self.font_thickness
        font_class_thickness = int(0.7*font_percentage_thickness)
        if self.font_thickness==0:
            font_percentage_thickness = 1
            font_class_thickness = 1

        ###DRAW SHOT WITH SHIFT###
        #init position of the first shot
        x_start = self.bloc_gap + shot_gap
        x_end = self.bloc_gap + shot_gap + shot_width
        y_start = self.headband_height + self.bloc_gap + shot_gap
        y_end = self.headband_height + self.bloc_gap + shot_gap + shot_height

        for k in range(len(probabilities)):
            images = self.snapshot[k]
            if images == []:
                self.ERROR = True
                self.empty_classe.append(str(k))
            elif y_end<self.height:
                #draw shots
                for n_shot in range(len(images)):
                    if y_end<self.height:
                        self.frame[y_start:y_end, x_start:x_end] = images[n_shot]
                        x_start = x_start + shot_shift
                        x_end = x_end + shot_shift
                        y_start = y_start + shot_shift
                        y_end = y_end + shot_shift
                cv2.putText(self.frame,f"class {k}",(x_start, y_end - shot_height + 2*shot_shift),self.font,font_class_scale,(0, 0, 255),font_class_thickness,cv2.LINE_AA)
                cv2.putText(self.frame,f"{n_shot+1}",(x_end - 4*shot_shift, y_end - shot_height + 2*shot_shift),self.font,font_class_scale,(0, 0, 255),font_class_thickness,cv2.LINE_AA)
                #draw level
                x_start = x_end - shot_shift + shot_gap
                y_start = y_end - shot_shift
                level_max = int(probabilities[k] * level_bar_height)
                for lvl in range(level_max):
                    level_start = (x_start , y_start - lvl)
                    level_end = (x_start + level_bar_width , y_start - (lvl+1))
                    cv2.rectangle(self.frame,level_start,level_end,percentage_to_color(lvl/level_bar_height),cv2.FILLED)
                #draw percentage
                x_start = x_start + shot_gap + level_bar_width
                y_start = y_start
                percentage_origin = (x_start , y_start)
                cv2.putText(self.frame,f"{int(np.round(100*probabilities[k].item()))}%",percentage_origin,self.font,font_percentage_scale,(0, 0, 255),font_percentage_thickness,cv2.LINE_AA)
                #update position for the next class
                x_start = self.bloc_gap + shot_gap
                x_end = x_start + shot_width
                y_start = y_start + shot_gap
                y_end = y_start + shot_height


    def draw_headband(self, under_band = 1):
        """
        parameters :
            under_band (float) : permit to draw a band under the headband : 1 (default) : draw the headband / 1.75 : draw the headband & an underband
        """      
        ###HEADBAND###
        headband_width = self.width
        headband_height = int(under_band*self.headband_height)
        cv2.rectangle(self.frame,(0,headband_height),(headband_width,0),(255,255,255),cv2.FILLED)

    def put_text(self, text, length_proportion, level = 1):
        """
        put some text in the interface
            parameters :
                text(string) : text to be added on the headband
                length_proportion (0<float<1): proportion of the length of the text relative to the frame, used to center the text
                level (int) : text writing level : 1 (default) : in the headband / 2 : in the underband 
        """
        text_length = int(self.Gscale*length_proportion*self.width)
        origin = (self.width//2 - text_length//2 , level*self.top_gap)
        cv2.putText(self.frame, text, origin, self.font, self.font_scale, (0, 0, 255), self.font_thickness, cv2.LINE_AA)   

    def put_fps_clock(self, fps, clock):
        """
        write fps on the left and clock on the right of the headband
        """
        #calculate the shift to shift the clock for every decade
        div = clock
        clock_shift_text = 0
        while div>=10:
            div = div/10
            clock_shift_text += 1

        #draw white rectangle to see the fps
        fps_start = (0 , self.headband_height)
        fps_end = (self.bloc_gap + int(self.Gscale*0.19*self.width), 0)
        cv2.rectangle(self.frame, fps_start, fps_end, (255,255,255), cv2.FILLED)
        #draw white rectangle to see the clock
        clock_origin = (self.width - self.bloc_gap - int(self.Gscale*( int(0.15*self.width) + clock_shift_text*int(0.019*self.width) )) , self.top_gap)
        clock_start = (clock_origin[0] - self.bloc_gap , self.headband_height)
        clock_end = (self.width , 0)
        cv2.rectangle(self.frame, clock_start, clock_end, (255,255,255), cv2.FILLED)

        #put fps on the frame
        cv2.putText(self.frame, f'fps : {fps}', (self.bloc_gap , self.top_gap), self.font, self.font_scale, (0, 0, 0), self.font_thickness, cv2.LINE_AA)
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
        image_label = cv2.resize(frame_to_add,(self.shot_width, self.shot_height),interpolation=cv2.INTER_AREA)
        self.snapshot[classe].append(image_label)
        print(f" Class {classe} registered. Number of shots : {self.get_number_snapshot(classe)}")

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



def ms(value,width):
        return '{:^{width}.2f}'.format(1000*value,width=width)

class Timer:
    """
    Class to display timers on the terminal
    Easy to use :
        - columns : a dictionary in which keys and values will be display on the terminal 
        - tic() : save instantaneous time. If init = True, save initial time
        - toc(step) : save the duration since tic() and associate with the step in the dictionary "columns". Save also instantaneous time like tic().
                      If end = true, calculate and save total time
        - timer() : display the dictionary on the terminal, i.e. texts and associate values in ms
        - fps_() : calculate and save fps
        - reset() : reset of Timer
    For example : 
                    T.tic() # instantaneous time
                    frame = preprocess(frame)
                    T.toc("PREPROCESS") # calculate the duration of preprocess() and save the value in the dictionary as "PREPROCESS"
                    features = backbone(frame)
                    T.toc("BACKBONE") # calculate the duration of backbone() and save the value in the dictionary as "PREPROCESS"
    """
    def __init__(self,period=0.1):
        self.period = period
        self.columns = {"FPS":0,"TOTAL TIME (ms)":0}
        self.saved_columns = {"FPS":0,"TOTAL TIME (ms)":0}
        self.time = time.time()
        self.wait = time.time()
        self.initial_time = 0
        self.total_time = 0
        self.fps = 0
        self.display = True
        self.ON = True

    def timer(self):
        if self.ON:
            if self.display:
                self.display = False
                print("|",end="")
                for txt in self.columns:
                    print(" ",txt," |",end="")
                print("")
            if(time.time() - self.wait > self.period):
                self.wait = time.time()
                print("\r",end="")
                print("|",end="")
                for txt in self.columns:
                    l1 = len(txt)+4 #length of texts
                    print(ms(self.columns[txt],width=l1),end="")
                    print("|",end="")
    
    def tic(self,init=False):
        self.time = time.time()
        if init:
            self.initial_time = time.time()

    def toc(self,step,end=False):
        if not end:
            self.columns[step] = time.time() - self.time
        else:
            self.total_time = time.time() - self.initial_time
            self.columns[step] = self.total_time
        self.time = time.time()

    def fps_(self):
        self.fps = 1/(1000*self.total_time)
    
    def reset(self):
        self.columns = self.saved_columns.copy()
        self.time = time.time()
        self.wait = time.time()
        self.initial_time = 0
        self.total_time = 0
        self.fps = 0
        self.display = True
        self.ON = True