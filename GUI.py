import pygame
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