import pygame
from pygame.locals import *
from pygame import mixer
#for importing world data
import json
import os
from os import path

pygame.mixer.pre_init(44100, -16, 2, 512)
mixer.init()
pygame.init()

#frame rate
clock = pygame.time.Clock()
fps = 60

screen_width = 800
screen_height = 800

screen = pygame.display.set_mode((screen_width,screen_height))
pygame.display.set_caption('Trial Beta')

#font
font_score = pygame.font.SysFont('Bauhaus 93', 30)
font = pygame.font.SysFont('Bauhaus 93', 70)
#global variable

tile_size = 40
game_over = 0
main_menu = True
level = 1
#max no of levels
max_levels = 5
score = 0
bg_size = (800,800)
cloud_size=(200,200)
button_height = 50
button_length = 140

#define color
white = (255, 255, 255)
blue = (0, 0, 255)
# imp-> in screen positive y means going down, top left is origin

#load images
bg_img = pygame.image.load('bg.png')
bg_img = pygame.transform.scale(bg_img,bg_size)
cloud_img = pygame.image.load('cloud.png')
cloud_img = pygame.transform.scale(cloud_img,cloud_size)
restart_img = pygame.image.load('restart_img.png')
restart_img = pygame.transform.scale(restart_img,(button_length,button_height))
start_img = pygame.image.load('start_img.png')
start_img = pygame.transform.scale(start_img,(230,70))
exit_img = pygame.image.load('exit_img.png')
exit_img = pygame.transform.scale(exit_img,(230,70))

#load sound
coin_fx =  pygame.mixer.Sound('coin.wav')
coin_fx.set_volume(0.5)
jump_fx =  pygame.mixer.Sound('jump.wav')
jump_fx.set_volume(0.5)
gameover_fx =  pygame.mixer.Sound('game_over.wav')
gameover_fx.set_volume(0.5)
#bg music, no variable needed cuz always playing
pygame.mixer.music.load('music.wav')
pygame.mixer.music.play(-1, 0.0, 5000)

#score counter
def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x,y))

#function to reset level
def reset_level(level):
    Player.reset(100,screen_height-90)
    slime_group.empty()
    lava_group.empty()
    exit_group.empty()
    coin_group.empty()
    score_coin = coin(tile_size // 2, tile_size // 2 + 5)
    coin_group.add(score_coin)
    platform_group.empty()
    if os.path.exists(f'level{level}_data.txt'):
        level_file = open(f'level{level}_data.txt', 'r')
        world_data = json.load(level_file)
    # print(world_data)
    World = world(world_data)

    return World

class button():
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.clicked = False
    def draw(self):
        action = False

        #mouse position
        pos = pygame.mouse.get_pos()

        #if on button
        if self.rect.collidepoint(pos):
            #if clicked (0 -> left mouse button)
            if pygame.mouse.get_pressed()[0]==1 and self.clicked == False:
                action = True
                self.clicked = True
        #if mouse released, reset button so it can be clicked again
        if pygame.mouse.get_pressed()[0]==0:
            self.clicked = False

        #draw  button
        screen.blit(self.image, self.rect)
        return action
    
class player():
    def __init__(self,x,y):
        self.reset(x,y)

    def update(self, game_over):
        dx=0
        dy=0
        walk_cooldown = 4
        col_thresh = 20

        if game_over == 0:
            #keybinds
            key = pygame.key.get_pressed()
            if key[pygame.K_LEFT]:
                dx-=5
                self.counter += 1
                self.direction = -1
            if key[pygame.K_RIGHT]:
                dx+=5
                self.counter += 1
                self.direction = 1
            if key[pygame.K_LEFT] == False and key[pygame.K_RIGHT] == False:
                self.counter = 0
                self.index = 0
                if self.direction == 1:
                    self.image = self.images_right[self.index]
                if self.direction == -1:
                    self.image = self.images_left[self.index]
            if key[pygame.K_SPACE] and self.jumping==False and self.in_air == False:
                jump_fx.play()
                self.vel_y = -17
                self.jumping=True
            if key[pygame.K_SPACE]==False and self.jumping==True:
                self.jumping=False

            #animation
            
            if self.counter > walk_cooldown :
                self.counter = 0
                self.index += 1
                if self.index >= len(self.images_right):
                    self.index = 0
                if self.direction == 1:
                    self.image = self.images_right[self.index]
                if self.direction == -1:
                    self.image = self.images_left[self.index]
            
            #gravity
            self.vel_y+=1
            if self.vel_y > 10:
                self.vel_y = 10
            dy += self.vel_y

            #colllision
            self.in_air = True
            for tile in World.tile_list:
                #x collison
                if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0

                #y direction (checking if collision will happen if player's postiion is updated)
                if tile[1].colliderect(self.rect.x, self.rect.y + dy , self.width, self.height):
                    #if block is above
                    if self.vel_y < 0:
                        dy = tile[1].bottom - self.rect.top 
                        self.vel_y = 0

                    #if block is below
                    elif self.vel_y >= 0:
                        dy = tile[1].top - self.rect.bottom
                        self.vel_y = 0
                        self.in_air = False
            
            #enemy collison
            if pygame.sprite.spritecollide(self, slime_group, False):
                game_over = -1
                gameover_fx.play()
            if pygame.sprite.spritecollide(self, lava_group, False):
                game_over = -1
                gameover_fx.play()
                            
            #exit collison
            if pygame.sprite.spritecollide(self, exit_group, False):
                game_over = 1

            #moving platform collision
            for platform in platform_group:
                #x collison
                if platform.rect.colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0
                #y collison
                if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                    #check if below platform
                    if abs((self.rect.top + dy) - platform.rect.bottom) < col_thresh:
                        self.vel_y = 0
                        dy = platform.rect.bottom - self.rect.top
                    #check if above platform
                    elif abs((self.rect.bottom + dy) - platform.rect.top) < col_thresh:
                        self.rect.bottom = platform.rect.top - 1
                        self.in_air = False
                        dy = 0
                    #move horizontally with platform
                    if platform.move_x != 0:
                        self.rect.x += platform.move_direction   

            #update coordinates
            self.rect.x += dx
            self.rect.y += dy

        elif game_over == -1:
            self.image = self.dead_image
            draw_text('GAME OVER! ', font, blue, (screen_width//2)-175, screen_height//2 - 150)
            if self.rect.y > 200:
                self.rect.y -= 5

        screen.blit(self.image,self.rect)
        return game_over
    
    def reset(self, x, y):
        self.images_right = []
        self.images_left = []
        #index for above image list
        self.index = 0
        #to check time between two images
        self.counter = 0
        for num in range(1,10):
            img_right = pygame.image.load(f'manright{num}.png')
            img_right = pygame.transform.scale(img_right,(25,50))
            img_left = pygame.transform.flip(img_right, True, False)
            self.images_right.append(img_right)
            self.images_left.append(img_left)
        self.dead_image = pygame.image.load('dead.png')
        self.dead_image = pygame.transform.scale(self.dead_image,(25,50))
        self.image = self.images_right[self.index]
        # img = pygame.image.load('man.png') -> standing man
        # self.image = pygame.transform.scale(img,(40,80))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        #get width of image for collision check
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.vel_y = 0
        self.jumping = False
        self.direction = 0
        self.in_air = True

class world():
        
    def __init__(self , data):
        self.tile_list = []
        #load images
        grass_img = pygame.image.load('grass.png')
        grass_center_img = pygame.image.load('grassCenter.png')
        grass_center_rounded_img = pygame.image.load('grassCenter_rounded.png')
        grass_center_img = pygame.image.load('grassCenter.png')
        grass_cliffleft_img = pygame.image.load('grassCliffLeft.png')
        grass_cliffright_img = pygame.image.load('grassCliffRight.png')
        grass_left_img = pygame.image.load('grassLeft.png')
        grass_mid_img = pygame.image.load('grassMid.png')
        grass_right_img = pygame.image.load('grassRight.png')
        

        row_count = 0
        for row in data:
            col_count = 0
            for col in row:
                if col == 1:
                    img = pygame.transform.scale(grass_img,(tile_size,tile_size))
                    img_rect=img.get_rect()
                    img_rect.x=col_count*tile_size
                    img_rect.y=row_count*tile_size
                    tile = (img,img_rect)
                    self.tile_list.append(tile)
                if col == 2:
                    img = pygame.transform.scale(grass_center_img,(tile_size,tile_size))
                    img_rect=img.get_rect()
                    img_rect.x=col_count*tile_size
                    img_rect.y=row_count*tile_size
                    tile = (img,img_rect)
                    self.tile_list.append(tile)
                if col == 3:
                    img = pygame.transform.scale(grass_cliffleft_img,(tile_size,tile_size))
                    img_rect=img.get_rect()
                    img_rect.x=col_count*tile_size
                    img_rect.y=row_count*tile_size
                    tile = (img,img_rect)
                    self.tile_list.append(tile)
                if col == 4:
                    img = pygame.transform.scale(grass_mid_img,(tile_size,tile_size))
                    img_rect=img.get_rect()
                    img_rect.x=col_count*tile_size
                    img_rect.y=row_count*tile_size
                    tile = (img,img_rect)
                    self.tile_list.append(tile)
                if col == 9:
                    img = pygame.transform.scale(grass_cliffright_img,(tile_size,tile_size))
                    img_rect=img.get_rect()
                    img_rect.x=col_count*tile_size
                    img_rect.y=row_count*tile_size
                    tile = (img,img_rect)
                    self.tile_list.append(tile)
                #enemies
                if col == 7:
                    slime = enemy(col_count*tile_size, row_count*tile_size+13)
                    slime_group.add(slime)
                if col == 8:
                    Lava = lava(col_count*tile_size, row_count*tile_size + (tile_size // 2))
                    lava_group.add(Lava) 
                if col == 5:
                    Exit = exit(col_count*tile_size, row_count*tile_size - (tile_size // 2))
                    exit_group.add(Exit)

                if col == 6:
                    Coin = coin(col_count*tile_size + (tile_size // 2), row_count*tile_size + (tile_size // 2))
                    coin_group.add(Coin)
                if col == 10:
                    #horizontal
                    Platform = platform(col_count*tile_size, row_count*tile_size, 1, 0)
                    platform_group.add(Platform)
                if col == 11:
                    #vertical
                    Platform = platform(col_count*tile_size, row_count*tile_size, 0, 1)
                    platform_group.add(Platform)
                
                col_count+=1
            row_count+=1
                    # img = pygame.transform.scale(grass_center_img,(tile_size,tile_size))
                    # img = pygame.transform.scale(grass_center_rounded_img,(tile_size,tile_size))
            
    def draw(self):
         for tile in self.tile_list:
            screen.blit(tile[0],tile[1])

#moving platform
class platform(pygame.sprite.Sprite):
    def __init__(self,x, y, move_x, move_y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('grassHalf.png')
        self.image = pygame.transform.scale(img, (tile_size, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_counter = 0
        self.move_direction = -1
        #to decide whether platform will move hprizontally or vertically
        self.move_x = move_x
        self.move_y = move_y

    def update(self):
        self.rect.x += self.move_direction*self.move_x
        self.rect.y += self.move_direction*self.move_y
        self.move_counter += 1
        if abs(self.move_counter) > 50 :
            self.move_direction *= -1
            self.move_counter *= -1

class enemy(pygame.sprite.Sprite):
    def __init__(self,x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('slimeWalk-1.png')
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_direction = -1
        self.move_counter = 0

    def update(self):
        self.rect.x += self.move_direction
        self.move_counter += 1
        if abs(self.move_counter) > 50 :
            self.move_direction *= -1
            self.image = pygame.image.load(f'slimeWalk{self.move_direction}.png')
            self.move_counter *= -1

class lava(pygame.sprite.Sprite):
    def __init__(self,x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('lava.png')
        self.image = pygame.transform.scale(img, (tile_size,tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class coin(pygame.sprite.Sprite):
    def __init__(self,x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('coin.png')
        self.image = pygame.transform.scale(img, (tile_size ,tile_size ))
        self.rect = self.image.get_rect()
        self.rect.center = (x,y)

class exit(pygame.sprite.Sprite):
    def __init__(self,x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('exit.png')
        self.image = pygame.transform.scale(img, (tile_size,int(tile_size * 1.5)))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
            
# world_data = [
#     [2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2],
#     [2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,5,2],
#     [2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,2],
#     [2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,3,4,2],
#     [2,0,3,9,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2],
#     [2,0,0,0,0,0,0,0,0,0,0,0,0,0,7,0,0,0,0,2],
#     [2,0,0,0,3,9,0,0,0,0,0,3,4,4,4,4,4,9,0,2],
#     [2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2],
#     [2,0,0,0,0,0,0,3,9,0,0,0,0,0,0,0,0,0,0,2],
#     [2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2],
#     [2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2],
#     [2,0,0,3,4,4,9,0,0,0,0,0,0,0,0,0,0,0,0,2],
#     [2,0,0,0,0,0,0,0,0,0,7,0,0,7,0,0,0,0,0,2],
#     [2,0,0,0,0,0,0,0,3,4,4,4,4,4,4,9,0,0,0,2],
#     [2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2],
#     [2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,3,2],
#     [2,0,0,0,0,0,0,0,0,0,0,0,4,0,0,0,0,0,0,2],
#     [2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4,4,0,0,2],
#     [2,0,0,0,0,0,0,0,0,4,8,8,8,8,4,2,2,4,8,2],
#     [2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2],

# ]

Player = player(85,screen_height-90)
platform_group = pygame.sprite.Group()
slime_group = pygame.sprite.Group()
lava_group = pygame.sprite.Group()
coin_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()
#coin dummy for score representation (can't be collected cuz off the screen)
score_coin = coin(tile_size // 2, tile_size // 2 + 5)
coin_group.add(score_coin)

#load level data
if os.path.exists(f'level{level}_data.txt'):
    level_file = open(f'level{level}_data.txt', 'r')
    world_data = json.load(level_file)
    # print(world_data)

World = world(world_data)
restart_button = button(screen_width // 2 - 50, screen_height // 2, restart_img)
start_button = button(screen_width // 2 - 250, screen_height // 2, start_img)
exit_button = button(screen_width // 2 + 50, screen_height // 2, exit_img)

run = True
while run:
    clock.tick(fps)
    screen.blit(bg_img, (0,0))
    screen.blit(cloud_img,(200,200))
    screen.blit(cloud_img,(400,12))
    screen.blit(cloud_img,(600,600))
    screen.blit(cloud_img,(150,550))
    screen.blit(cloud_img,(0,0))

    if main_menu == True:
        if exit_button.draw():
            run = False
        if start_button.draw():
            main_menu = False
    else:
        World.draw()

        if game_over == 0:
            #if game is running, enemies are moving,otherwise stop
            slime_group.update()
            platform_group.update()
            #update score
            #check if coin is collected
            #the true in parameter erases coin on collision (its false in all other type of collision)
            if pygame.sprite.spritecollide(Player, coin_group, True):
                score += 1
                coin_fx.play()
            draw_text(' X ' + str(score), font_score, white, tile_size - 10, 10)

        platform_group.draw(screen)
        slime_group.draw(screen)
        lava_group.draw(screen)
        exit_group.draw(screen)
        coin_group.draw(screen)

        game_over = Player.update(game_over)

        #if player dies
        if game_over == -1:
            if restart_button.draw():
                world_data = []
                level = 1
                World = reset_level(level)
                game_over = 0
                score = 0

        #level over
        if game_over == 1:
            #update level
            level += 1
            #update game
            if level <= max_levels:
                world_data = []
                World = reset_level(level)
                game_over = 0
            else:
                draw_text('YOU WIN!' , font , blue, (screen_width//2)-175, screen_height//2 - 150)
                if restart_button.draw():
                    level = 1
                    world_data = []
                    World = reset_level(level)
                    game_over = 0
                    score = 0

    #event handler
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
    # grid()
    pygame.display.update()



pygame.quit()