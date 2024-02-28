"""
GUI.py

Setup for the GUI for PCC. Adds all the sprites and initilizes the display


"""


import pygame

#Import constants from CONSTANTS.PY
from CONSTANTS import *


#pygame classes
class adjustbutton(pygame.sprite.Sprite):
    def __init__(self,color,width,height,points,TL=(0,0)):
        super().__init__() #not sure what this does - probably gathers sprite class initialization data...
        
        self.TL=TL
        self.image=pygame.Surface([width,height])
        self.image.fill(WHITE)
        pygame.draw.polygon(self.image,color,points)
        self.rect = self.image.get_rect()
        self.rect.x,self.rect.y=(self.TL[0],self.TL[1])
        
class labeledbutton(pygame.sprite.Sprite):
    def __init__(self,color1,color2,width,height,label,TL=(0,0)):
        super().__init__() #not sure what this does - probably gathers sprite class initialization data...

        self.width=width
        self.height=height
        self.TL=TL
        self.label=label
        self.color1=color1
        self.color2=color2
        
        buttonlabel = font.render(label,True,color2)
        buttonlabel_rect= buttonlabel.get_rect()
        buttonlabel_rect.center=(int(width/2),int(height/2))
        
        self.image=pygame.Surface([width,height])
        self.image.fill(color1)
        pygame.draw.rect(self.image,color1,(0,0,width,height))
        self.image.blit(buttonlabel,buttonlabel_rect)
        self.rect = self.image.get_rect()
        self.rect.x,self.rect.y=(self.TL[0],self.TL[1])
    
    def relocate(self,x,y):
        self.TL=(x,y)

        buttonlabel = font.render(self.label,True,self.color2)
        buttonlabel_rect= buttonlabel.get_rect()
        buttonlabel_rect.center=(int(self.width/2),int(self.height/2))
        
        self.image=pygame.Surface([self.width,self.height])
        self.image.fill(self.color1)
        pygame.draw.rect(self.image,self.color1,(0,0,self.width,self.height))
        self.image.blit(buttonlabel,buttonlabel_rect)
        self.rect = self.image.get_rect()
        self.rect.x,self.rect.y=(self.TL[0],self.TL[1])
    
    def update(self,color1,color2,label):
        self.color1=color1
        self.color2=color2
        self.label=label
        
        buttonlabel = font.render(label,True,color2)
        buttonlabel_rect= buttonlabel.get_rect()
        buttonlabel_rect.center=(int(self.width/2),int(self.height/2))
        self.image=pygame.Surface([self.width,self.height])
        self.image.fill(color1)
        pygame.draw.rect(self.image,color1,(0,0,self.width,self.height))
        self.image.blit(buttonlabel,buttonlabel_rect)
        self.rect = self.image.get_rect()
        self.rect.x,self.rect.y=(self.TL[0],self.TL[1])

    def update_left(self,color1,color2,label):
            self.color1=color1
            self.color2=color2
            self.label=label
            
            buttonlabel = font.render(label,True,color2)
            buttonlabel_rect= buttonlabel.get_rect()
            buttonlabel_rect.midleft=(10,int(self.height/2))
            self.image=pygame.Surface([self.width,self.height])
            self.image.fill(color1)
            pygame.draw.rect(self.image,color1,(0,0,self.width,self.height))
            self.image.blit(buttonlabel,buttonlabel_rect)
            self.rect = self.image.get_rect()
            self.rect.x,self.rect.y=(self.TL[0],self.TL[1])


def trianglepoints(direction):
    if direction=='up':
        return [(10,0),(0,10),(20,10)]
    elif direction=='down':
        return [(10,10),(0,0),(20,0)]
    elif direction=='left':
        return [(0,10),(10,0),(10,20)]
    elif direction=='right':
        return [(0,0),(0,20),(10,10)]

#%% setup display
pygame.init()
font=pygame.font.SysFont('lucidaconsole',18)
DISPLAYSURF = pygame.display.set_mode(ScreenSize)
pygame.display.set_caption('Plethysmography Command Center')
#%%
DISPLAYSURF.fill(BACKGROUND_COLOR)
## prepare sprites
control_sizes={'vertical':{'inc':(20,10),'dec':(20,10),'reset':(20,20),'float':(95,20)}}
control_offset={'verticalA':{'inc':(-30,-10),'dec':(-30,40),'reset':(-30,0),'float':(-95,20)},
                'verticalB':{'inc':(-30,-10),'dec':(-30,40),'reset':(-30,0),'float':(-35,20)},
                'verticalC':{'inc':(-30,200),'dec':(-30,250),'reset':(-30,210),'float':(-95,230)},
                'verticalD':{'inc':(-30,200),'dec':(-30,250),'reset':(-30,210),'float':(-35,230)},
                'horizontalA':{'inc':(-10,10),'dec':(40,10),'reset':(0,10),'float':(20,10)}}

#title and version box
title_version_box = labeledbutton(WHITE,BLACK,300,25,'PCC __version__',TL=(400,0))

#g1 controls
g1_ymax_inc=adjustbutton(GREEN,
                         control_sizes['vertical']['inc'][0],
                         control_sizes['vertical']['inc'][1],
                         trianglepoints('up'),
                         (g1_TL[0]+control_offset['verticalA']['inc'][0],
                          g1_TL[1]+control_offset['verticalA']['inc'][1]))
g1_ymax_dec=adjustbutton(RED,
                         control_sizes['vertical']['dec'][0],
                         control_sizes['vertical']['dec'][1],
                         trianglepoints('down'),
                         (g1_TL[0]+control_offset['verticalA']['dec'][0],
                          g1_TL[1]+control_offset['verticalA']['dec'][1]))
g1_ymax_reset=labeledbutton(BLUE,WHITE,
                            control_sizes['vertical']['reset'][0],
                            control_sizes['vertical']['reset'][1],
                            'R',(g1_TL[0]+control_offset['verticalA']['reset'][0],
                                 g1_TL[1]+control_offset['verticalA']['reset'][1]))
g1_ymax_float=labeledbutton(BLACK,WHITE,
                            control_sizes['vertical']['float'][0],
                            control_sizes['vertical']['float'][1],
                            '{:#.3F}'.format(g1_y_minmax[1]),(g1_TL[0]+control_offset['verticalA']['float'][0],
                                 g1_TL[1]+control_offset['verticalA']['float'][1]))
g1_ymin_inc=adjustbutton(GREEN,
                         control_sizes['vertical']['inc'][0],
                         control_sizes['vertical']['inc'][1],
                         trianglepoints('up'),
                         (g1_TL[0]+control_offset['verticalC']['inc'][0],
                          g1_TL[1]+control_offset['verticalC']['inc'][1]))
g1_ymin_dec=adjustbutton(RED,
                         control_sizes['vertical']['dec'][0],
                         control_sizes['vertical']['dec'][1],
                         trianglepoints('down'),
                         (g1_TL[0]+control_offset['verticalC']['dec'][0],
                          g1_TL[1]+control_offset['verticalC']['dec'][1]))
g1_ymin_reset=labeledbutton(BLUE,WHITE,
                            control_sizes['vertical']['reset'][0],
                            control_sizes['vertical']['reset'][1],
                            'R',(g1_TL[0]+control_offset['verticalC']['reset'][0],
                                 g1_TL[1]+control_offset['verticalC']['reset'][1]))
g1_ymin_float=labeledbutton(BLACK,WHITE,
                            control_sizes['vertical']['float'][0],
                            control_sizes['vertical']['float'][1],
                            '{:#.3F}'.format(g1_y_minmax[0]),(g1_TL[0]+control_offset['verticalC']['float'][0],
                                 g1_TL[1]+control_offset['verticalC']['float'][1]))

#g2 controls
#
g2_ymax_inc=adjustbutton(GREEN,
                         control_sizes['vertical']['inc'][0],
                         control_sizes['vertical']['inc'][1],
                         trianglepoints('up'),
                         (g2_TL[0]+control_offset['verticalA']['inc'][0],
                          g2_TL[1]+control_offset['verticalA']['inc'][1]))
g2_ymax_dec=adjustbutton(RED,
                         control_sizes['vertical']['dec'][0],
                         control_sizes['vertical']['dec'][1],
                         trianglepoints('down'),
                         (g2_TL[0]+control_offset['verticalA']['dec'][0],
                          g2_TL[1]+control_offset['verticalA']['dec'][1]))
g2_ymax_reset=labeledbutton(BLUE,WHITE,
                            control_sizes['vertical']['reset'][0],
                            control_sizes['vertical']['reset'][1],
                            'R',(g2_TL[0]+control_offset['verticalA']['reset'][0],
                                 g2_TL[1]+control_offset['verticalA']['reset'][1]))
g2_ymax_float=labeledbutton(BLACK,WHITE,
                            control_sizes['vertical']['float'][0],
                            control_sizes['vertical']['float'][1],
                            '{:#.3F}'.format(g2_y_minmax[1]),(g2_TL[0]+control_offset['verticalA']['float'][0],
                                 g2_TL[1]+control_offset['verticalA']['float'][1]))
g2_ymin_inc=adjustbutton(GREEN,
                         control_sizes['vertical']['inc'][0],
                         control_sizes['vertical']['inc'][1],
                         trianglepoints('up'),
                         (g2_TL[0]+control_offset['verticalC']['inc'][0],
                          g2_TL[1]+control_offset['verticalC']['inc'][1]))

g2_ymin_dec=adjustbutton(RED,
                         control_sizes['vertical']['dec'][0],
                         control_sizes['vertical']['dec'][1],
                         trianglepoints('down'),
                         (g2_TL[0]+control_offset['verticalC']['dec'][0],
                          g2_TL[1]+control_offset['verticalC']['dec'][1]))
g2_ymin_reset=labeledbutton(BLUE,WHITE,
                            control_sizes['vertical']['reset'][0],
                            control_sizes['vertical']['reset'][1],
                            'R',(g2_TL[0]+control_offset['verticalC']['reset'][0],
                                 g2_TL[1]+control_offset['verticalC']['reset'][1]))
g2_ymin_float=labeledbutton(BLACK,WHITE,
                            control_sizes['vertical']['float'][0],
                            control_sizes['vertical']['float'][1],
                            '{:#.3F}'.format(g2_y_minmax[0]),(g2_TL[0]+control_offset['verticalC']['float'][0],
                                 g2_TL[1]+control_offset['verticalC']['float'][1]))

#g3 controls
g3_ymax_inc=adjustbutton(GREEN,
                         control_sizes['vertical']['inc'][0],
                         control_sizes['vertical']['inc'][1],
                         trianglepoints('up'),
                         (g3_TL[0]+control_offset['verticalA']['inc'][0],
                          g3_TL[1]+control_offset['verticalA']['inc'][1]))
g3_ymax_dec=adjustbutton(RED,
                         control_sizes['vertical']['dec'][0],
                         control_sizes['vertical']['dec'][1],
                         trianglepoints('down'),
                         (g3_TL[0]+control_offset['verticalA']['dec'][0],
                          g3_TL[1]+control_offset['verticalA']['dec'][1]))
g3_ymax_reset=labeledbutton(BLUE,WHITE,
                            control_sizes['vertical']['reset'][0],
                            control_sizes['vertical']['reset'][1],
                            'R',(g3_TL[0]+control_offset['verticalA']['reset'][0],
                                 g3_TL[1]+control_offset['verticalA']['reset'][1]))
g3_ymax_float=labeledbutton(BLACK,WHITE,
                            control_sizes['vertical']['float'][0],
                            control_sizes['vertical']['float'][1],
                            '{:#.3F}'.format(g3_y_minmax[1]),(g3_TL[0]+control_offset['verticalA']['float'][0],
                                 g3_TL[1]+control_offset['verticalA']['float'][1]))
g3_ymin_inc=adjustbutton(GREEN,
                         control_sizes['vertical']['inc'][0],
                         control_sizes['vertical']['inc'][1],
                         trianglepoints('up'),
                         (g3_TL[0]+control_offset['verticalC']['inc'][0],
                          g3_TL[1]+control_offset['verticalC']['inc'][1]))

g3_ymin_dec=adjustbutton(RED,
                         control_sizes['vertical']['dec'][0],
                         control_sizes['vertical']['dec'][1],
                         trianglepoints('down'),
                         (g3_TL[0]+control_offset['verticalC']['dec'][0],
                          g3_TL[1]+control_offset['verticalC']['dec'][1]))
g3_ymin_reset=labeledbutton(BLUE,WHITE,
                            control_sizes['vertical']['reset'][0],
                            control_sizes['vertical']['reset'][1],
                            'R',(g3_TL[0]+control_offset['verticalC']['reset'][0],
                                 g3_TL[1]+control_offset['verticalC']['reset'][1]))
g3_ymin_float=labeledbutton(BLACK,WHITE,
                            control_sizes['vertical']['float'][0],
                            control_sizes['vertical']['float'][1],
                            '{:#.3F}'.format(g3_y_minmax[0]),(g3_TL[0]+control_offset['verticalC']['float'][0],
                                 g3_TL[1]+control_offset['verticalC']['float'][1]))

#increment adjuster
inc_inc=adjustbutton(GREEN,
                         control_sizes['vertical']['inc'][0],
                         control_sizes['vertical']['inc'][1],
                         trianglepoints('up'),
                         (inc_TL[0]+control_offset['verticalA']['inc'][0],
                          inc_TL[1]+control_offset['verticalA']['inc'][1]))
inc_dec=adjustbutton(RED,
                         control_sizes['vertical']['dec'][0],
                         control_sizes['vertical']['dec'][1],
                         trianglepoints('down'),
                         (inc_TL[0]+control_offset['verticalA']['dec'][0],
                          inc_TL[1]+control_offset['verticalA']['dec'][1]))
inc_reset=labeledbutton(BLUE,WHITE,
                            control_sizes['vertical']['reset'][0],
                            control_sizes['vertical']['reset'][1],
                            'R',(inc_TL[0]+control_offset['verticalA']['reset'][0],
                                 inc_TL[1]+control_offset['verticalA']['reset'][1]))
inc_float=labeledbutton(BLACK,WHITE,
                            control_sizes['vertical']['float'][0],
                            control_sizes['vertical']['float'][1],
                            '{:#.3F}'.format(increment),(inc_TL[0]+control_offset['verticalA']['float'][0],
                                 inc_TL[1]+control_offset['verticalA']['float'][1]))

#baseline flow adjuster
baseline_flow_inc=adjustbutton(GREEN,
                         control_sizes['vertical']['inc'][0],
                         control_sizes['vertical']['inc'][1],
                         trianglepoints('up'),
                         (baseline_flow_TL[0]+control_offset['verticalA']['inc'][0],
                          baseline_flow_TL[1]+control_offset['verticalA']['inc'][1]))
baseline_flow_dec=adjustbutton(RED,
                         control_sizes['vertical']['dec'][0],
                         control_sizes['vertical']['dec'][1],
                         trianglepoints('down'),
                         (baseline_flow_TL[0]+control_offset['verticalA']['dec'][0],
                          baseline_flow_TL[1]+control_offset['verticalA']['dec'][1]))
baseline_flow_reset=labeledbutton(BLUE,WHITE,
                                  control_sizes['vertical']['reset'][0],
                                  control_sizes['vertical']['reset'][1],
                                  'R',
                                  (baseline_flow_TL[0]+control_offset['verticalA']['reset'][0],
                                   baseline_flow_TL[1]+control_offset['verticalA']['reset'][1]))
baseline_flow_float=labeledbutton(BLACK,WHITE,
                            control_sizes['vertical']['float'][0],
                            control_sizes['vertical']['float'][1],
                            '{:#.3F}'.format(baseline_flow),(baseline_flow_TL[0]+control_offset['verticalB']['float'][0],
                                 baseline_flow_TL[1]+control_offset['verticalB']['float'][1]))

#thresh flow adjuster
thresh_flow_inc=adjustbutton(GREEN,
                         control_sizes['vertical']['inc'][0],
                         control_sizes['vertical']['inc'][1],
                         trianglepoints('up'),
                         (thresh_flow_TL[0]+control_offset['verticalA']['inc'][0],
                          thresh_flow_TL[1]+control_offset['verticalA']['inc'][1]))
thresh_flow_dec=adjustbutton(RED,
                         control_sizes['vertical']['dec'][0],
                         control_sizes['vertical']['dec'][1],
                         trianglepoints('down'),
                         (thresh_flow_TL[0]+control_offset['verticalA']['dec'][0],
                          thresh_flow_TL[1]+control_offset['verticalA']['dec'][1]))
thresh_flow_reset=labeledbutton(BLUE,WHITE,
                            control_sizes['vertical']['reset'][0],
                            control_sizes['vertical']['reset'][1],
                            'R',(thresh_flow_TL[0]+control_offset['verticalA']['reset'][0],
                                 thresh_flow_TL[1]+control_offset['verticalA']['reset'][1]))
thresh_flow_float=labeledbutton(BLACK,WHITE,
                            control_sizes['vertical']['float'][0],
                            control_sizes['vertical']['float'][1],
                            '{:#.3F}'.format(thresh_flow),(thresh_flow_TL[0]+control_offset['verticalB']['float'][0],
                                 thresh_flow_TL[1]+control_offset['verticalB']['float'][1]))

#thresh2 flow adjuster
thresh2_flow_inc=adjustbutton(GREEN,
                         control_sizes['vertical']['inc'][0],
                         control_sizes['vertical']['inc'][1],
                         trianglepoints('up'),
                         (thresh2_flow_TL[0]+control_offset['verticalA']['inc'][0],
                          thresh2_flow_TL[1]+control_offset['verticalA']['inc'][1]))
thresh2_flow_dec=adjustbutton(RED,
                         control_sizes['vertical']['dec'][0],
                         control_sizes['vertical']['dec'][1],
                         trianglepoints('down'),
                         (thresh2_flow_TL[0]+control_offset['verticalA']['dec'][0],
                          thresh2_flow_TL[1]+control_offset['verticalA']['dec'][1]))
thresh2_flow_reset=labeledbutton(BLUE,WHITE,
                            control_sizes['vertical']['reset'][0],
                            control_sizes['vertical']['reset'][1],
                            'R',(thresh2_flow_TL[0]+control_offset['verticalA']['reset'][0],
                                 thresh2_flow_TL[1]+control_offset['verticalA']['reset'][1]))
thresh2_flow_float=labeledbutton(BLACK,WHITE,
                            control_sizes['vertical']['float'][0],
                            control_sizes['vertical']['float'][1],
                            '{:#.3F}'.format(thresh2_flow),(thresh2_flow_TL[0]+control_offset['verticalA']['float'][0],
                                 thresh2_flow_TL[1]+control_offset['verticalA']['float'][1]))

#baseline vol adjuster
baseline_vol_inc=adjustbutton(GREEN,
                         control_sizes['vertical']['inc'][0],
                         control_sizes['vertical']['inc'][1],
                         trianglepoints('up'),
                         (baseline_vol_TL[0]+control_offset['verticalA']['inc'][0],
                          baseline_vol_TL[1]+control_offset['verticalA']['inc'][1]))
baseline_vol_dec=adjustbutton(RED,
                         control_sizes['vertical']['dec'][0],
                         control_sizes['vertical']['dec'][1],
                         trianglepoints('down'),
                         (baseline_vol_TL[0]+control_offset['verticalA']['dec'][0],
                          baseline_vol_TL[1]+control_offset['verticalA']['dec'][1]))
baseline_vol_reset=labeledbutton(BLUE,WHITE,
                            control_sizes['vertical']['reset'][0],
                            control_sizes['vertical']['reset'][1],
                            'R',
                            (baseline_vol_TL[0]+control_offset['verticalA']['reset'][0],
                             baseline_vol_TL[1]+control_offset['verticalA']['reset'][1]))
baseline_vol_float=labeledbutton(BLACK,WHITE,
                            control_sizes['vertical']['float'][0],
                            control_sizes['vertical']['float'][1],
                            '{:#.3F}'.format(baseline_vol),(baseline_vol_TL[0]+control_offset['verticalB']['float'][0],
                                 baseline_vol_TL[1]+control_offset['verticalB']['float'][1]))

#thresh flow adjuster
thresh_vol_inc=adjustbutton(GREEN,
                         control_sizes['vertical']['inc'][0],
                         control_sizes['vertical']['inc'][1],
                         trianglepoints('up'),
                         (thresh_vol_TL[0]+control_offset['verticalA']['inc'][0],
                          thresh_vol_TL[1]+control_offset['verticalA']['inc'][1]))
thresh_vol_dec=adjustbutton(RED,
                         control_sizes['vertical']['dec'][0],
                         control_sizes['vertical']['dec'][1],
                         trianglepoints('down'),
                         (thresh_vol_TL[0]+control_offset['verticalA']['dec'][0],
                          thresh_vol_TL[1]+control_offset['verticalA']['dec'][1]))
thresh_vol_reset=labeledbutton(BLUE,WHITE,
                            control_sizes['vertical']['reset'][0],
                            control_sizes['vertical']['reset'][1],
                            'R',(thresh_vol_TL[0]+control_offset['verticalA']['reset'][0],
                                 thresh_vol_TL[1]+control_offset['verticalA']['reset'][1]))
thresh_vol_float=labeledbutton(BLACK,WHITE,
                            control_sizes['vertical']['float'][0],
                            control_sizes['vertical']['float'][1],
                            '{:#.3F}'.format(thresh_vol),(thresh_vol_TL[0]+control_offset['verticalB']['float'][0],
                                 thresh_vol_TL[1]+control_offset['verticalB']['float'][1]))

#baseline ecg adjuster
baseline_ecg_inc=adjustbutton(GREEN,
                         control_sizes['vertical']['inc'][0],
                         control_sizes['vertical']['inc'][1],
                         trianglepoints('up'),
                         (baseline_ecg_TL[0]+control_offset['verticalA']['inc'][0],
                          baseline_ecg_TL[1]+control_offset['verticalA']['inc'][1]))
baseline_ecg_dec=adjustbutton(RED,
                         control_sizes['vertical']['dec'][0],
                         control_sizes['vertical']['dec'][1],
                         trianglepoints('down'),
                         (baseline_ecg_TL[0]+control_offset['verticalA']['dec'][0],
                          baseline_ecg_TL[1]+control_offset['verticalA']['dec'][1]))
baseline_ecg_reset=labeledbutton(BLUE,WHITE,
                            control_sizes['vertical']['reset'][0],
                            control_sizes['vertical']['reset'][1],
                            'R',(baseline_ecg_TL[0]+control_offset['verticalA']['reset'][0],
                                 baseline_ecg_TL[1]+control_offset['verticalA']['reset'][1]))
baseline_ecg_float=labeledbutton(BLACK,WHITE,
                            control_sizes['vertical']['float'][0],
                            control_sizes['vertical']['float'][1],
                            '{:#.3F}'.format(baseline_ecg),(baseline_ecg_TL[0]+control_offset['verticalB']['float'][0],
                                 baseline_ecg_TL[1]+control_offset['verticalB']['float'][1]))

#noise ecg adjuster
noise_ecg_inc=adjustbutton(GREEN,
                         control_sizes['vertical']['inc'][0],
                         control_sizes['vertical']['inc'][1],
                         trianglepoints('up'),
                         (noise_ecg_TL[0]+control_offset['verticalA']['inc'][0],
                          noise_ecg_TL[1]+control_offset['verticalA']['inc'][1]))
noise_ecg_dec=adjustbutton(RED,
                         control_sizes['vertical']['dec'][0],
                         control_sizes['vertical']['dec'][1],
                         trianglepoints('down'),
                         (noise_ecg_TL[0]+control_offset['verticalA']['dec'][0],
                          noise_ecg_TL[1]+control_offset['verticalA']['dec'][1]))
noise_ecg_reset=labeledbutton(BLUE,WHITE,
                            control_sizes['vertical']['reset'][0],
                            control_sizes['vertical']['reset'][1],
                            'R',(noise_ecg_TL[0]+control_offset['verticalA']['reset'][0],
                                 noise_ecg_TL[1]+control_offset['verticalA']['reset'][1]))
noise_ecg_float=labeledbutton(BLACK,WHITE,
                            control_sizes['vertical']['float'][0],
                            control_sizes['vertical']['float'][1],
                            '{:#.1F}'.format(noise_ecg),(noise_ecg_TL[0]+control_offset['verticalA']['float'][0],
                                 noise_ecg_TL[1]+control_offset['verticalA']['float'][1]))

#absthresh ecg adjuster
absthresh_ecg_inc=adjustbutton(GREEN,
                         control_sizes['vertical']['inc'][0],
                         control_sizes['vertical']['inc'][1],
                         trianglepoints('up'),
                         (absthresh_ecg_TL[0]+control_offset['verticalA']['inc'][0],
                          absthresh_ecg_TL[1]+control_offset['verticalA']['inc'][1]))
absthresh_ecg_dec=adjustbutton(RED,
                         control_sizes['vertical']['dec'][0],
                         control_sizes['vertical']['dec'][1],
                         trianglepoints('down'),
                         (absthresh_ecg_TL[0]+control_offset['verticalA']['dec'][0],
                          absthresh_ecg_TL[1]+control_offset['verticalA']['dec'][1]))
absthresh_ecg_reset=labeledbutton(BLUE,WHITE,
                            control_sizes['vertical']['reset'][0],
                            control_sizes['vertical']['reset'][1],
                            'R',(absthresh_ecg_TL[0]+control_offset['verticalA']['reset'][0],
                                 absthresh_ecg_TL[1]+control_offset['verticalA']['reset'][1]))
absthresh_ecg_float=labeledbutton(BLACK,WHITE,
                            control_sizes['vertical']['float'][0],
                            control_sizes['vertical']['float'][1],
                            '{:#.3F}'.format(absthresh_ecg),(absthresh_ecg_TL[0]+control_offset['verticalB']['float'][0],
                                 absthresh_ecg_TL[1]+control_offset['verticalB']['float'][1]))


#thresh ecg1 adjuster
thresh_ecg1_inc=adjustbutton(GREEN,
                         control_sizes['vertical']['inc'][0],
                         control_sizes['vertical']['inc'][1],
                         trianglepoints('up'),
                         (thresh_ecg1_TL[0]+control_offset['verticalA']['inc'][0],
                          thresh_ecg1_TL[1]+control_offset['verticalA']['inc'][1]))
thresh_ecg1_dec=adjustbutton(RED,
                         control_sizes['vertical']['dec'][0],
                         control_sizes['vertical']['dec'][1],
                         trianglepoints('down'),
                         (thresh_ecg1_TL[0]+control_offset['verticalA']['dec'][0],
                          thresh_ecg1_TL[1]+control_offset['verticalA']['dec'][1]))
thresh_ecg1_reset=labeledbutton(BLUE,WHITE,
                            control_sizes['vertical']['reset'][0],
                            control_sizes['vertical']['reset'][1],
                            'R',(thresh_ecg1_TL[0]+control_offset['verticalA']['reset'][0],
                                 thresh_ecg1_TL[1]+control_offset['verticalA']['reset'][1]))
thresh_ecg1_float=labeledbutton(BLACK,WHITE,
                            control_sizes['vertical']['float'][0],
                            control_sizes['vertical']['float'][1],
                            '{:#.2F}'.format(thresh_ecg1),(thresh_ecg1_TL[0]+control_offset['verticalA']['float'][0],
                                 thresh_ecg1_TL[1]+control_offset['verticalA']['float'][1]))

thresh_ecg2_inc=adjustbutton(GREEN,
                         control_sizes['vertical']['inc'][0],
                         control_sizes['vertical']['inc'][1],
                         trianglepoints('up'),
                         (thresh_ecg2_TL[0]+control_offset['verticalA']['inc'][0],
                          thresh_ecg2_TL[1]+control_offset['verticalA']['inc'][1]))
thresh_ecg2_dec=adjustbutton(RED,
                         control_sizes['vertical']['dec'][0],
                         control_sizes['vertical']['dec'][1],
                         trianglepoints('down'),
                         (thresh_ecg2_TL[0]+control_offset['verticalA']['dec'][0],
                          thresh_ecg2_TL[1]+control_offset['verticalA']['dec'][1]))
thresh_ecg2_reset=labeledbutton(BLUE,WHITE,
                            control_sizes['vertical']['reset'][0],
                            control_sizes['vertical']['reset'][1],
                            'R',(thresh_ecg2_TL[0]+control_offset['verticalA']['reset'][0],
                                 thresh_ecg2_TL[1]+control_offset['verticalA']['reset'][1]))
thresh_ecg2_float=labeledbutton(BLACK,WHITE,
                            control_sizes['vertical']['float'][0],
                            control_sizes['vertical']['float'][1],
                            '{:#.2F}'.format(thresh_ecg2),(thresh_ecg2_TL[0]+control_offset['verticalA']['float'][0],
                                 thresh_ecg2_TL[1]+control_offset['verticalA']['float'][1]))
box_stream_lag=labeledbutton(BACKGROUND_COLOR,RED,
                             150,25,
                             '{:#.3F}'.format(stream_lag),
                                 (ScreenSize[0]-150,ScreenSize[1]-25))
PLETHFILT_TOGGLE=labeledbutton(RED,BLACK,200,25,'FILT FLOW',PLETHFILT_TL)
ECGFILT_TOGGLE=labeledbutton(RED,BLACK,200,25,'FILT ECG',ECGFILT_TL)
INVERT_FLOW_TOGGLE=labeledbutton(WHITE,BLACK,200,25,'Inv Flow:{}'.format(INVERT_FLOW),INVERT_FLOW_TL)
INVERT_ECG_TOGGLE=labeledbutton(WHITE,BLACK,200,25,'Inv ECG:{}'.format(INVERT_ECG),INVERT_ECG_TL)

box_minimum_resus_time=labeledbutton(WHITE,BLACK,300,25,'RECOVERY:{:d}/{:d})'.format(int(current_recovery),int(minimum_resus_time)),minimum_resus_time_TL)

box_SLB_trigger=labeledbutton(YELLOW,BLACK,300,25,'SLB: {:#.2F} sec'.format(SLB_Trigger),SLB_trigger_TL)
box_CALL_DEATH_trigger=labeledbutton(YELLOW,BLACK,300,25,'CALL DEATH: {:#.2F} min'.format(CALL_DEATH_trigger/60),CALL_DEATH_trigger_TL)
box_HR_recovery_thresh=labeledbutton(YELLOW,BLACK,300,25,'HR recover: *NA* %',HR_recovery_thresh_TL)
box_BPM_recovery_thresh=labeledbutton(YELLOW,BLACK,300,25,'BPM recover: *NA* %',BPM_recovery_thresh_TL)
box_avgBPM_thresh=labeledbutton(YELLOW,BLACK,300,25,'avg BPM: *NA* bpm',avgBPM_thresh_TL)
box_cvTT_thresh=labeledbutton(YELLOW,BLACK,300,25,'CV TT: *NA* ratio',cvTT_thresh_TL)
box_avgHR_thresh=labeledbutton(YELLOW,BLACK,300,25,'avg HR: *NA* bpm',avgHR_thresh_TL)
box_avgRR_thresh=labeledbutton(YELLOW,BLACK,300,25,'avg RR: *NA* sec',avgRR_thresh_TL)
box_cvRR_thresh=labeledbutton(YELLOW,BLACK,300,25,'CV RR: *NA* ratio',cvRR_thresh_TL)
box_BSD_thresh=labeledbutton(YELLOW,BLACK,300,25,'Base Drift: *NA* V',BSD_thresh_TL)
box_DVTV_thresh=labeledbutton(YELLOW,BLACK,300,25,'DVTV: *NA* ratio',DVTV_thresh_TL)
box_QB_duration=labeledbutton(YELLOW,BLACK,300,25,'min QB: *NA* sec',QB_duration_TL)

box_BT=labeledbutton(WHITE,BLUE,BT_xySize[0],BT_xySize[1],'BT:*NA* C',BT_TL)
box_CT=labeledbutton(WHITE,BLUE,CT_xySize[0],CT_xySize[1],'CT:*NA* C',CT_TL)
box_RH=labeledbutton(WHITE,BLUE,RH_xySize[0],RH_xySize[1],'RH:*NA* %',RH_TL)
box_O2=labeledbutton(WHITE,BLUE,O2_xySize[0],O2_xySize[1],'O2:*NA** %',O2_TL)
box_CO2=labeledbutton(WHITE,BLUE,CO2_xySize[0],CO2_xySize[1],'CO2: *NA* %',CO2_TL)
#derived param displays
box_BPM=labeledbutton(BLUE,WHITE,BPM_xySize[0],BPM_xySize[1],'BPM:*NA*',BPM_TL)

box_TV=labeledbutton(BLUE,WHITE,TV_xySize[0],TV_xySize[1],'TV:*NA*',TV_TL)
box_HR=labeledbutton(BLUE,WHITE,HR_xySize[0],HR_xySize[1],'HR:*NA*',HR_TL)
box_baseBPM=labeledbutton(GREEN,BLACK,baseBPM_xySize[0],baseBPM_xySize[1],'base BPM:*NA*',baseBPM_TL)

box_baseTV=labeledbutton(GREEN,BLACK,baseTV_xySize[0],baseTV_xySize[1],'base TV:*NA*',baseTV_TL)
box_baseHR=labeledbutton(GREEN,BLACK,baseHR_xySize[0],baseHR_xySize[1],'base HR:*NA*',baseHR_TL)
box_sincelastbreath=labeledbutton(WHITE,GREEN,sincelastbreath_xySize[0],sincelastbreath_xySize[1],
                                  'SLB: *NA* sec',sincelastbreath_TL)
box_qual_bouts=labeledbutton(YELLOW,BLACK,qual_bouts_xySize[0],qual_bouts_xySize[1],'bouts:*NA*',qual_bouts_TL)
box_qual_dur=labeledbutton(YELLOW,BLACK,qual_dur_xySize[0],qual_dur_xySize[1],'duration:*NA*',qual_dur_TL)
box_qual_test=labeledbutton(WHITE,BLACK,qual_test_xySize[0],qual_test_xySize[1],'',qual_test_TL)

graph1=labeledbutton(WHITE,WHITE,g1_xySize[0],g1_xySize[1],'',g1_TL)
graph2=labeledbutton(WHITE,WHITE,g2_xySize[0],g2_xySize[1],'',g2_TL)
graph3=labeledbutton(WHITE,WHITE,g3_xySize[0],g3_xySize[1],'',g3_TL)

FLOW_LABEL=labeledbutton(WHITE,BLACK,125,25,'Flow',g1_TL)
VOL_LABEL=labeledbutton(WHITE,BLACK,125,25,'Volume',g2_TL)
ECG_LABEL=labeledbutton(WHITE,BLACK,125,25,'ECG',g3_TL)

box_MODE=labeledbutton(BLACK,WHITE,250,25,Mode_dict[Current_Mode],(ScreenSize[0]-275,0))
box_NEXT=labeledbutton(GREEN,WHITE,25,25,'>>',(ScreenSize[0]-25,0))
box_duration=labeledbutton(BLACK,RED,250,25,'*NA* sec',(0,ScreenSize[1]-25))

#$$$$ scoreboard

SLB_Trigger_Setter=labeledbutton(WHITE,BLACK,SLB_Trigger_Setter_xySize[0],SLB_Trigger_Setter_xySize[1],
                                 'SLB_Trigger: {}sec'.format(SLB_Trigger),SLB_Trigger_Setter_TL)
Challenge_Counter=labeledbutton(WHITE,BLACK,Challenge_Counter_xySize[0],Challenge_Counter_xySize[1],
                                'Challenge #: __', Challenge_Counter_TL)
CurrentChallengeCO2_Timer=labeledbutton(WHITE,BLACK,CurrentChallengeCO2_Timer_xySize[0],CurrentChallengeCO2_Timer_xySize[1],
                                           'CO2 Time: ___sec',CurrentChallengeCO2_Timer_TL)
CurrentChallengeRecovery_Timer=labeledbutton(WHITE,BLACK,CurrentChallengeRecovery_Timer_xySize[0],CurrentChallengeRecovery_Timer_xySize[1],
                                                'Rec Time: ___sec',CurrentChallengeRecovery_Timer_TL)

Position_RA=labeledbutton(BLACK,WHITE,Position_RA_xySize[0],Position_RA_xySize[1],
                          'RA position: {}'.format(Arduino_Function_Constants['Position_RA']),
                          Position_RA_TL)
Position_Gas=labeledbutton(BLACK,WHITE,Position_Gas_xySize[0],Position_Gas_xySize[1],
                                        'Gas position: {}'.format(Arduino_Function_Constants['Position_Gas']),
                                        Position_Gas_TL)
Duration_Cal=labeledbutton(BLACK,WHITE,Duration_Cal_xySize[0],Duration_Cal_xySize[1],
                           'Cal dur: {}'.format(Arduino_Function_Constants['Duration_Cal']),
                           Duration_Cal_TL)
Duration_Prefill=labeledbutton(BLACK,WHITE,Duration_Cal_xySize[0],Duration_Cal_xySize[1],
                               'Prefill dur: {}'.format(Arduino_Function_Constants['Duration_Prefill']),
                               Duration_Prefill_TL)
Duration_Challenge_Delay=labeledbutton(BLACK,WHITE,Duration_Challenge_Delay_xySize[0],Duration_Challenge_Delay_xySize[1],
                                       'Challenge Delay: {}'.format(Challenge_Delay),
                                       Position_Challenge_Delay_TL)
Text_Challenge_Phrase=labeledbutton(BLACK,WHITE,Text_Challenge_Phrase_xySize[0],Text_Challenge_Phrase_xySize[1],
                                    'Phrase: {}'.format(Challenge_phrase),
                                    Position_Challenge_Phrase_TL)

Serial_Abort=labeledbutton(RED,BLACK,Serial_Abort_xySize[0],Serial_Abort_xySize[1],
                           'ABORT!',Serial_Abort_TL)
Serial_Rec_OR=labeledbutton(GREEN,BLACK,Serial_Rec_OR_xySize[0],Serial_Rec_OR_xySize[1],
                            'ORide!',Serial_Rec_OR_TL)
Serial_ShutDown=labeledbutton(BLACK,WHITE,Serial_ShutDown_xySize[0],Serial_ShutDown_xySize[1],
                              'ShutDown',Serial_ShutDown_TL)

finish_startup=labeledbutton(BLACK,WHITE,finish_startup_xySize[0],finish_startup_xySize[1],
                             '',finish_startup_TL)

SerialOutTester=labeledbutton(WHITE,BLACK,SerialOutTester_xySize[0],SerialOutTester_xySize[1],
                              'Serial Out',SerialOutTester_TL)

SO1=labeledbutton(DGREY,WHITE,SO1_xySize[0],SO1_xySize[1],
                  ':',SO1_TL)
SO2=labeledbutton(DGREY,WHITE,SO2_xySize[0],SO2_xySize[1],
                  ':',SO2_TL)
SO3=labeledbutton(DGREY,WHITE,SO3_xySize[0],SO3_xySize[1],
                  ':',SO3_TL)
SO4=labeledbutton(DGREY,WHITE,SO4_xySize[0],SO4_xySize[1],
                  ':',SO4_TL)
SO5=labeledbutton(DGREY,WHITE,SO5_xySize[0],SO5_xySize[1],
                  ':',SO5_TL)
SO6=labeledbutton(DGREY,WHITE,SO6_xySize[0],SO6_xySize[1],
                  ':',SO6_TL)
SO7=labeledbutton(DGREY,WHITE,SO7_xySize[0],SO7_xySize[1],
                  ':',SO7_TL)
SO8=labeledbutton(DGREY,WHITE,SO8_xySize[0],SO8_xySize[1],
                  ':',SO8_TL)
SO9=labeledbutton(DGREY,WHITE,SO9_xySize[0],SO9_xySize[1],
                  ':',SO9_TL)

#$$$$
                          
box_SAVE=labeledbutton(BLACK,WHITE,450,25,'SAVE',(ScreenSize[0]-650,ScreenSize[1]-25))
box_oldSave=labeledbutton(RED,WHITE,100,25,'Old SAVE',(450,ScreenSize[1]-25))
box_NOTIFICATION=labeledbutton(DGREY,WHITE,500,25,'NOTIFICATIONS-OFF',(ScreenSize[0]-650,ScreenSize[1]-50))

box_Synch=labeledbutton(RED,WHITE,250,25,'Synch Stream',(ScreenSize[0]-275,25))
box_mode_select={}
box_mode_times={}
for i in Mode_dict:
    box_mode_select[i]=labeledbutton(BLACK,WHITE,300,25,'{}:{:#.2F}'.format(Mode_dict[i],Mode_timing[i]/60),(ScreenSize[0]-325,25*i+50))
    box_mode_times[i]=labeledbutton(VIOLET,WHITE,25,25,'t',(ScreenSize[0]-25,25*i+50))

#prep sprite list
sprite_list=pygame.sprite.Group()

sprite_list.add(title_version_box)

sprite_list.add(box_oldSave)

sprite_list.add(box_MODE)

sprite_list.add(box_Synch)
for i in Mode_dict:
    sprite_list.add(box_mode_select[i])
    sprite_list.add(box_mode_times[i])


sprite_list.add(box_NEXT)
sprite_list.add(box_duration)

sprite_list.add(graph1)
sprite_list.add(graph2)
sprite_list.add(graph3)

sprite_list.add(box_SLB_trigger)
sprite_list.add(box_CALL_DEATH_trigger)
sprite_list.add(box_HR_recovery_thresh)
sprite_list.add(box_BPM_recovery_thresh)
sprite_list.add(box_avgBPM_thresh)
sprite_list.add(box_cvTT_thresh)
sprite_list.add(box_avgHR_thresh)
sprite_list.add(box_avgRR_thresh)
sprite_list.add(box_cvRR_thresh)
sprite_list.add(box_BSD_thresh)
sprite_list.add(box_DVTV_thresh)
sprite_list.add(box_QB_duration)

sprite_list.add(FLOW_LABEL)
sprite_list.add(VOL_LABEL)
sprite_list.add(ECG_LABEL)

sprite_list.add(g1_ymax_inc)
sprite_list.add(g1_ymax_dec)
sprite_list.add(g1_ymax_reset)
sprite_list.add(g1_ymax_float)
sprite_list.add(g1_ymin_inc)
sprite_list.add(g1_ymin_dec)
sprite_list.add(g1_ymin_reset)
sprite_list.add(g1_ymin_float)

sprite_list.add(g2_ymax_inc)
sprite_list.add(g2_ymax_dec)
sprite_list.add(g2_ymax_reset)
sprite_list.add(g2_ymax_float)
sprite_list.add(g2_ymin_inc)
sprite_list.add(g2_ymin_dec)
sprite_list.add(g2_ymin_reset)
sprite_list.add(g2_ymin_float)

sprite_list.add(g3_ymax_inc)
sprite_list.add(g3_ymax_dec)
sprite_list.add(g3_ymax_reset)
sprite_list.add(g3_ymax_float)
sprite_list.add(g3_ymin_inc)
sprite_list.add(g3_ymin_dec)
sprite_list.add(g3_ymin_reset)
sprite_list.add(g3_ymin_float)

sprite_list.add(baseline_flow_inc)
sprite_list.add(baseline_flow_dec)
sprite_list.add(baseline_flow_reset)
sprite_list.add(baseline_flow_float)

sprite_list.add(baseline_vol_inc)
sprite_list.add(baseline_vol_dec)
sprite_list.add(baseline_vol_reset)
sprite_list.add(baseline_vol_float)

sprite_list.add(baseline_ecg_inc)
sprite_list.add(baseline_ecg_dec)
sprite_list.add(baseline_ecg_reset)
sprite_list.add(baseline_ecg_float)

sprite_list.add(noise_ecg_inc)
sprite_list.add(noise_ecg_dec)
sprite_list.add(noise_ecg_reset)
sprite_list.add(noise_ecg_float)

sprite_list.add(thresh_flow_inc)
sprite_list.add(thresh_flow_dec)
sprite_list.add(thresh_flow_reset)
sprite_list.add(thresh_flow_float)

sprite_list.add(thresh2_flow_inc)
sprite_list.add(thresh2_flow_dec)
sprite_list.add(thresh2_flow_reset)
sprite_list.add(thresh2_flow_float)

sprite_list.add(thresh_vol_inc)
sprite_list.add(thresh_vol_dec)
sprite_list.add(thresh_vol_reset)
sprite_list.add(thresh_vol_float)

sprite_list.add(thresh_ecg1_inc)
sprite_list.add(thresh_ecg1_dec)
sprite_list.add(thresh_ecg1_reset)
sprite_list.add(thresh_ecg1_float)

sprite_list.add(absthresh_ecg_inc)
sprite_list.add(absthresh_ecg_dec)
sprite_list.add(absthresh_ecg_reset)
sprite_list.add(absthresh_ecg_float)

sprite_list.add(thresh_ecg2_inc)
sprite_list.add(thresh_ecg2_dec)
sprite_list.add(thresh_ecg2_reset)
sprite_list.add(thresh_ecg2_float)

sprite_list.add(inc_inc)
sprite_list.add(inc_dec)
sprite_list.add(inc_reset)
sprite_list.add(inc_float)

sprite_list.add(ECGFILT_TOGGLE)
sprite_list.add(PLETHFILT_TOGGLE)
sprite_list.add(box_minimum_resus_time)
sprite_list.add(INVERT_FLOW_TOGGLE)
sprite_list.add(INVERT_ECG_TOGGLE)

sprite_list.add(box_BT)
sprite_list.add(box_CT)
sprite_list.add(box_RH)
sprite_list.add(box_O2)
sprite_list.add(box_CO2)
#derived param displays
sprite_list.add(box_BPM)
sprite_list.add(box_TV)
sprite_list.add(box_HR)
sprite_list.add(box_baseBPM)
sprite_list.add(box_baseTV)
sprite_list.add(box_baseHR)
sprite_list.add(box_sincelastbreath)
sprite_list.add(box_qual_bouts)
sprite_list.add(box_qual_dur)
sprite_list.add(box_qual_test)
sprite_list.add(box_SAVE)
sprite_list.add(box_NOTIFICATION)
sprite_list.add(box_stream_lag)

#$$$$ scoreboard
sprite_list.add(Position_RA)
sprite_list.add(Position_Gas)
sprite_list.add(Duration_Cal)
sprite_list.add(Duration_Prefill)
sprite_list.add(Duration_Challenge_Delay)
sprite_list.add(Text_Challenge_Phrase)
sprite_list.add(SLB_Trigger_Setter)
sprite_list.add(Challenge_Counter)
sprite_list.add(CurrentChallengeCO2_Timer)
sprite_list.add(CurrentChallengeRecovery_Timer)
sprite_list.add(Serial_Abort)
sprite_list.add(Serial_Rec_OR)
sprite_list.add(Serial_ShutDown)
sprite_list.add(SerialOutTester)
sprite_list.add(SO1)
sprite_list.add(SO2)
sprite_list.add(SO3)
sprite_list.add(SO4)
sprite_list.add(SO5)
sprite_list.add(SO6)
sprite_list.add(SO7)
sprite_list.add(SO8)
sprite_list.add(SO9)

#$$$$

sprite_list.draw(DISPLAYSURF)
