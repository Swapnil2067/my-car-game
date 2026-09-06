# =============================================================================
# SWAPNIL THE RIDER — ASPHALT 9 ARCADE LEGENDS EDITION
# Features: Triple Nitro Stages, Drift Physics, Air-Time Barrel Rolls,
# Dynamic Police Chases, 50-Car Garage, & Embedded Theme Soundtrack.
# =============================================================================

import json, math, os, random, time, wave, struct
from pathlib import Path
import pygame

# Initialize Pygame core subsystems
pygame.init()
try:
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.mixer.init()
    AUDIO_OK = True
except pygame.error:
    AUDIO_OK = False

# Define directories, filepaths, and core display constants
BASE_DIR = Path(__file__).resolve().parent
ASSET_DIR = BASE_DIR / 'assets'
SAVE_FILE = BASE_DIR / 'savegame.json'
MUSIC_FILE = BASE_DIR / 'Swapnil The Racer (1).mp3'
LOGICAL_W, LOGICAL_H, FPS = 1200, 760, 60
WIDTH, HEIGHT = LOGICAL_W, LOGICAL_H
DISPLAY = None
FULLSCREEN = True

def create_display(caption):
    """Creates and scales the main application display surface."""
    global DISPLAY
    flags = pygame.FULLSCREEN | pygame.SCALED if FULLSCREEN else 0
    DISPLAY = pygame.display.set_mode((LOGICAL_W, LOGICAL_H), flags)
    pygame.display.set_caption(caption)
    return DISPLAY

def present(surface):
    """Refreshes the display buffers to present rendered frames."""
    pygame.display.flip()

def toggle_fullscreen():
    """Toggles the game view between windowed and fullscreen modes."""
    global FULLSCREEN, DISPLAY
    FULLSCREEN = not FULLSCREEN
    flags = pygame.FULLSCREEN | pygame.SCALED if FULLSCREEN else 0
    DISPLAY = pygame.display.set_mode((LOGICAL_W, LOGICAL_H), flags)

def safe_selected_car(value):
    """Ensures the currently chosen car string maps safely to valid data assets."""
    if isinstance(value, (list, tuple)):
        value = value[0] if value else DEFAULT['selected_car']
    if not isinstance(value, str) or value not in ALL_CARS:
        value = DEFAULT['selected_car']
    return value

# Color palette definitions for UI elements and track graphics
WHITE=(245,248,255); BLACK=(8,10,14); GOLD=(244,194,65); CYAN=(35,225,255)
GREEN=(55,225,125); RED=(245,72,80); ORANGE=(255,155,55); PURPLE=(185,100,255)
GREY=(135,145,160); DARK=(16,21,30); PANEL=(22,29,40)

# Full 50-car roster for the Asphalt-style garage system
ALL_CARS = [
'box_truck.png','cargo_truck_blue.png','cargo_truck_green.png','cargo_truck_red.png','city_bus.png','delivery_van.png',
'dump_truck.png','fuel_tanker.png','jeep_black.png','jeep_olive.png','log_truck.png','luxury_car_black.png','luxury_car_blue.png',
'luxury_car_red.png','luxury_car_silver.png','luxury_car_white.png','monster_truck_blue.png','monster_truck_green.png',
'monster_truck_purple.png','monster_truck_red.png','monster_truck_yellow.png','pickup_truck.png','pickup_truck_blue.png',
'player_car_blue.png','player_car_green.png','player_car_red.png','player_car_white.png','player_car_yellow.png',
'police_car_black.png','police_car_black_white.png','police_car_white.png','police_suv.png','police_van.png','school_bus.png',
'sports_car_black.png','sports_car_cyan.png','sports_car_gold.png','sports_car_lime.png','sports_car_orange.png','sports_car_purple.png',
'taxi_car.png','taxi_sedan.png','traffic_car_black.png','traffic_car_blue.png','traffic_car_green.png','traffic_car_orange.png',
'traffic_car_red.png','traffic_car_silver.png','traffic_car_white.png','traffic_car_yellow.png']
POLICE_CARS={'police_car_black.png','police_car_black_white.png','police_car_white.png','police_suv.png','police_van.png'}

CATEGORIES=['All','Player','Sports','Luxury','Monster Truck','Police','Traffic','Taxi','Truck','SUV / Pickup','Bus / Van']
TIMES=['Day','Midday','Night']
ROADS=['One-Way','Two-Way']
ENVIRONMENTS=['City','Desert','Marine','Forest','Snow','Canyon']

def category(f):
    """Categorizes vehicle assets based on their filename prefix."""
    n=f.lower()
    if n.startswith('player_car'): return 'Player'
    if n.startswith('police'): return 'Police'
    if n.startswith('monster'): return 'Monster Truck'
    if n.startswith('luxury'): return 'Luxury'
    if n.startswith('sports'): return 'Sports'
    if n.startswith('traffic'): return 'Traffic'
    if n.startswith('taxi'): return 'Taxi'
    if n in {'school_bus.png','city_bus.png','delivery_van.png'}: return 'Bus / Van'
    if 'truck' in n or n in {'fuel_tanker.png','log_truck.png'}: return 'Truck'
    if 'jeep' in n or 'pickup' in n: return 'SUV / Pickup'
    return 'Traffic'

def display_name(f):
    """Formats raw car filenames into clean displayable titles."""
    return Path(f).stem.replace('_',' ').title()

NON_POLICE=[x for x in ALL_CARS if x not in POLICE_CARS]
CAR_PRICES={n:250+i*55 for i,n in enumerate(ALL_CARS)}

DEFAULT={
    'coins':1500,'owned_cars':['player_car_blue.png'],'selected_car':'player_car_blue.png',
    'time_mode':'Midday','road_mode':'Two-Way','environment':'City',
    'upgrades':{'speed':1,'health':1,'nitro':1,'shield':1},'best_score':0,
    'leaderboard':[]
}

def load_state():
    """Loads saved game progression or falls back to default stats."""
    if not SAVE_FILE.exists(): return json.loads(json.dumps(DEFAULT))
    try:
        data=json.loads(SAVE_FILE.read_text(encoding='utf-8'))
        for k,v in DEFAULT.items():
            if k not in data: data[k]=v
        for k,v in DEFAULT['upgrades'].items(): data['upgrades'].setdefault(k,v)
        # Keep only valid leaderboard rows so a damaged save file cannot break the rankings screen.
        data['leaderboard'] = [row for row in data.get('leaderboard', []) if isinstance(row, dict)]
        data['leaderboard'] = data['leaderboard'][:10]
        data['owned_cars'] = [c for c in data.get('owned_cars', []) if isinstance(c, str) and c in ALL_CARS]
        if not data['owned_cars']: data['owned_cars'] = [DEFAULT['selected_car']]
        data['selected_car'] = safe_selected_car(data.get('selected_car'))
        if data['selected_car'] not in data['owned_cars']: data['selected_car'] = data['owned_cars'][0]
        return data
    except Exception: return json.loads(json.dumps(DEFAULT))

def save_state():
    """Saves player currencies, upgrades, and garage unlocks to disk."""
    try: SAVE_FILE.write_text(json.dumps(state,indent=2),encoding='utf-8')
    except Exception: pass

state=load_state()

def record_race(score, distance, coins, car_name):
    """Adds a completed race to the persistent top-ten rankings."""
    # Store the result as plain JSON data so it can be loaded on the next launch.
    state['leaderboard'].append({
        'score': int(score), 'distance': round(distance, 1), 'coins': int(coins),
        'car': display_name(car_name), 'environment': state['environment'],
        'time': time.strftime('%Y-%m-%d %H:%M')
    })
    # Sort by score first, then distance, and retain only the best ten runs.
    state['leaderboard'].sort(key=lambda row: (int(row.get('score', 0)), float(row.get('distance', 0))), reverse=True)
    state['leaderboard'] = state['leaderboard'][:10]
    save_state()

def make_swapnil_rider_song(path):
    """Procedurally builds and writes the synthwave theme song 'Swapnil The Rider'."""
    if path.exists(): return
    sr=44100; duration=36; total=sr*duration
    notes={'C4':261.63,'D4':293.66,'E4':329.63,'F4':349.23,'G4':392.00,'A4':440.00,'C5':523.25,'D5':587.33,'E5':659.25}
    melody=['E4','G4','A4','C5','A4','G4','E4','D4','E4','G4','C5','D5','E5','D5','C5','A4']
    beat=0.32
    raw=bytearray()
    for i in range(total):
        t=i/sr; idx=int(t/beat)%len(melody); note=notes[melody[idx]]; local=(t%beat)/beat
        env=min(1,local*8)*min(1,(1-local)*10)
        lead=math.sin(2*math.pi*note*t)*0.24 + math.sin(2*math.pi*note*1.5*t)*0.06
        bassnote=notes[['C4','A4','F4','G4'][int(t/(beat*4))%4]]/2
        bass=math.sin(2*math.pi*bassnote*t)*0.15 + math.cos(2*math.pi*(bassnote*.5)*t)*0.08
        phase=(t%(beat*2)); kenv=max(0,1-phase/0.14)
        kick=math.sin(2*math.pi*(80-40*phase/0.14)*t)*0.18*kenv
        hat=0.04*math.sin(2*math.pi*6000*t)*(1 if (int(t*12)%2)==0 else 0)
        sample=max(-1,min(1,(lead*env+bass+kick+hat)))
        s=int(sample*29000); raw += struct.pack('<hh',s,s)
    with wave.open(str(path),'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(raw)

def start_music():
    """Starts looping the background theme track during gameplay sessions."""
    if not AUDIO_OK or not MUSIC_FILE.exists(): return
    try:
        pygame.mixer.music.load(str(MUSIC_FILE)); pygame.mixer.music.set_volume(0.48); pygame.mixer.music.play(-1)
    except pygame.error: pass

def stop_music():
    """Halts playback of the background soundtrack."""
    if AUDIO_OK:
        try: pygame.mixer.music.stop()
        except pygame.error: pass

def rounded_rect(s,c,r,rad=10,w=0):
    """Draws a custom rounded rectangle shape onto a target surface."""
    pygame.draw.rect(s,c,pygame.Rect(r),width=w,border_radius=max(0,int(rad)))

def text(s,font,msg,pos,color=WHITE,center=False):
    """Renders and outputs text strings onto the screen surface."""
    im=font.render(str(msg),True,color); rr=im.get_rect(center=pos) if center else im.get_rect(topleft=pos); s.blit(im,rr); return rr

class Button:
    """Manages clickable UI controls, hover detection, and triggers actions."""
    def __init__(self,rect,label,callback,accent=CYAN,enabled=True):
        self.rect=pygame.Rect(rect); self.label=label; self.callback=callback; self.accent=accent; self.enabled=enabled; self.hover=False
    def draw(self,s,font):
        self.hover=self.rect.collidepoint(pygame.mouse.get_pos())
        fill=(62,82,100) if self.hover and self.enabled else (35,43,55)
        rounded_rect(s,fill,self.rect,9)
        rounded_rect(s,self.accent if self.enabled else GREY,self.rect,9,2)
        text(s,font,self.label,self.rect.center,WHITE if self.enabled else GREY,True)
    def handle(self,event):
        if self.enabled and event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and self.rect.collidepoint(event.pos):
            self.callback(); return True
        return False

class AssetBank:
    """Caches and loads vehicle textures, generating procedural fallbacks if missing."""
    def __init__(self): self.cache={}
    def fallback_car(self,name,size):
        image=pygame.Surface(size,pygame.SRCALPHA)
        colors={'sports':(225,65,72),'luxury':(190,195,205),'monster':(238,145,45),'police':(235,240,250),'taxi':(245,205,55),'truck':(205,125,55),'bus':(65,170,215),'van':(65,170,215),'jeep':(75,180,105),'pickup':(75,180,105),'traffic':(110,145,220),'player':(45,205,220)}
        lower=name.lower(); body=next((color for key,color in colors.items() if key in lower),(110,145,220))
        cx=size[0]//2; body_rect=pygame.Rect(max(4,cx-size[0]//3),8,max(12,size[0]*2//3),size[1]-16)
        rounded_rect(image,body,body_rect,10)
        pygame.draw.polygon(image,(190,225,240),[(body_rect.left+6,body_rect.top+22),(cx,body_rect.top+8),(body_rect.right-6,body_rect.top+22)])
        pygame.draw.rect(image,(35,48,62),(body_rect.left+8,body_rect.top+25,max(8,body_rect.width-16),22),border_radius=5)
        pygame.draw.rect(image,(35,48,62),(body_rect.left+8,body_rect.bottom-30,max(8,body_rect.width-16),20),border_radius=5)
        for wheel_y in (body_rect.top+25,body_rect.bottom-25):
            pygame.draw.circle(image,(18,21,28),(body_rect.left+2,wheel_y),6)
            pygame.draw.circle(image,(18,21,28),(body_rect.right-2,wheel_y),6)
        if 'police' in lower:
            pygame.draw.rect(image,RED,(cx-10,body_rect.top+3,9,5))
            pygame.draw.rect(image,CYAN,(cx+1,body_rect.top+3,9,5))
        return image
    def car(self,name,size):
        key=(name,size)
        if key in self.cache: return self.cache[key]
        p=ASSET_DIR/name
        if p.exists():
            try:
                im=pygame.image.load(str(p)).convert_alpha(); im=pygame.transform.smoothscale(im,size); self.cache[key]=im; return im
            except Exception: pass
        im=self.fallback_car(name,size); self.cache[key]=im; return im
assets=AssetBank()

class Particle:
    """Handles visual effects like nitro exhaust flames, sparks, and smoke plumes."""
    def __init__(self,x,y,vx,vy,life,size,kind='nitro'):
        self.x=x;self.y=y;self.vx=vx;self.vy=vy;self.life=life;self.max=life;self.size=size;self.kind=kind
    def update(self): self.x+=self.vx;self.y+=self.vy;self.vy+=0.05;self.life-=1
    def draw(self,s):
        if self.life<=0:return
        a=int(255*self.life/self.max); q=pygame.Surface((self.size*2+6,self.size*2+6),pygame.SRCALPHA)
        col={'nitro':(35,225,255,a),'shockwave':(255,100,255,a),'overdrive':(255,205,50,a),'coin':(255,205,60,a),'hit':(255,100,50,a),'smoke':(160,160,165,a)}.get(self.kind,(160,160,165,a))
        pygame.draw.circle(q,col,(self.size+3,self.size+3),self.size);s.blit(q,(self.x-self.size-3,self.y-self.size-3))

class Pickup(pygame.sprite.Sprite):
    """Spawns track collectibles such as coins, health kits, and nitro tanks."""
    def __init__(self,kind,x,y):
        super().__init__(); self.kind=kind; self.t=random.random()*6.28; self.image=pygame.Surface((38,38),pygame.SRCALPHA); self.rect=self.image.get_rect(center=(x,y)); self.redraw()
    def redraw(self):
        self.image.fill((0,0,0,0)); c={'coin':GOLD,'health':RED,'nitro':CYAN,'shield':PURPLE}[self.kind]
        pygame.draw.circle(self.image,c,(19,19),15,3)
        if self.kind=='coin': pygame.draw.circle(self.image,c,(19,19),8); text(self.image,pygame.font.SysFont('Arial',18,bold=True),'$',(19,20),BLACK,True)
        elif self.kind=='health': pygame.draw.rect(self.image,WHITE,(16,8,6,22));pygame.draw.rect(self.image,WHITE,(8,16,22,6))
        elif self.kind=='nitro': pygame.draw.polygon(self.image,WHITE,[(21,7),(11,21),(18,21),(14,31),(28,16),(21,16)])
        else: pygame.draw.circle(self.image,WHITE,(19,19),7,2)
    def update(self,world_speed): self.t+=.1;self.rect.y+=world_speed;self.rect.x+=int(math.sin(self.t)*.5); self.kill() if self.rect.top>HEIGHT+50 else None

class TrafficCar(pygame.sprite.Sprite):
    """Controls AI traffic vehicles moving across highway lanes."""
    def __init__(self,name,lane,oncoming,level):
        super().__init__();self.name=name;self.oncoming=oncoming
        cat=category(name); size=(84,132) if cat=='Monster Truck' else ((68,122) if cat in {'Truck','Bus / Van'} else (58,112))
        self.image=assets.car(name,size)
        if oncoming:self.image=pygame.transform.rotate(self.image,180)
        self.rect=self.image.get_rect(center=(LANES[lane],-150 if not oncoming else HEIGHT+160));self.speed=random.uniform(4.5,8.5)+level*.25 if not oncoming else random.uniform(8,13)+level*.4;self.drift=random.uniform(-.22,.22);self.passed=False
    def update(self,world_speed,level):
        self.rect.y += (world_speed-self.speed) if not self.oncoming else -(self.speed-world_speed*.18)
        self.rect.x += self.drift
        if self.rect.top>HEIGHT+180 or self.rect.bottom<-220:self.kill()

class PoliceCar(pygame.sprite.Sprite):
    """Controls aggressive police cruiser units that chase and track the player."""
    def __init__(self,lane,level):
        super().__init__();self.image=assets.car(random.choice(list(POLICE_CARS)),(64,116));self.rect=self.image.get_rect(center=(LANES[lane],-170));self.speed=6.5+level*.5;self.lane=lane;self.t=0
    def update(self,px,world_speed,level):
        self.rect.y += self.speed+world_speed*.5; self.rect.x += (1.3+level*.06) * (1 if self.rect.centerx<px else -1) if abs(self.rect.centerx-px)>8 else 0; self.t+=1
        if self.rect.top>HEIGHT+180:self.kill()

class Player(pygame.sprite.Sprite):
    """Manages player car movement, 3-tier Asphalt nitro mechanics, drifting, and physics."""
    def __init__(self,name):
        super().__init__(); name=safe_selected_car(name); self.name=name; st=car_stats(name); self.image=assets.car(name,(84,132) if category(name)=='Monster Truck' else (62,118));self.rect=self.image.get_rect(center=(LANES[2],565));self.x=float(self.rect.x)
        self.speed=0.;self.max_speed=15.0*st['speed']+state['upgrades']['speed']*.8;self.accel=.24*st['accel'];self.grip=st['grip'];self.max_health=10;self.health=self.max_health;self.max_nitro=100+state['upgrades']['nitro']*30;self.nitro=float(self.max_nitro);self.shield=0;self.inv=0;self.distance=0;self.nitro_mode=0;self.drift_charge=0
    def update(self,keys,particles):
        # Handle throttle and brake acceleration inputs
        if keys[pygame.K_w] or keys[pygame.K_UP]:self.speed=min(self.max_speed,self.speed+self.accel*1.6)
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:self.speed=max(0,self.speed-self.accel*2.5)
        else:self.speed=max(0,self.speed-.04)
        
        # ASPHALT 9 MULTI-TIER NITRO SYSTEM (Press SPACE/N to cycle Blue -> Shockwave -> Overdrive)
        if (keys[pygame.K_SPACE] or keys[pygame.K_n]) and self.nitro>0:
            self.nitro=max(0,self.nitro-0.8)
            if self.nitro>66: self.nitro_mode=3 # Shockwave Nitro (Purple/Gold invincibility burst)
            elif self.nitro>33: self.nitro_mode=2 # Overdrive Nitro (High speed yellow flames)
            else: self.nitro_mode=1 # Standard Blue Nitro
            
            # Apply nitro boost scaling
            boost_multiplier = {1: 1.5, 2: 2.1, 3: 3.2}[self.nitro_mode]
            self.speed=min(self.max_speed + (45.0 if self.nitro_mode==3 else 22.0), self.speed + boost_multiplier)
            
            # Emit matching nitro exhaust particles
            ptype = {'1':'nitro', '2':'overdrive', '3':'shockwave'}[str(self.nitro_mode)]
            for _ in range(3):
                particles.append(Particle(self.rect.centerx+random.randint(-18,18),self.rect.bottom,random.uniform(-2,2),random.uniform(4,8),22,random.randint(4,8),ptype))
        else:
            self.nitro_mode=0
            self.nitro=min(self.max_nitro,self.nitro+0.35)
            
        # Handle steering and drift slipstream mechanics
        steer=(keys[pygame.K_d] or keys[pygame.K_RIGHT])-(keys[pygame.K_a] or keys[pygame.K_LEFT])
        is_drifting = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        if is_drifting and steer!=0:
            self.drift_charge=min(100,self.drift_charge+1.5)
            self.nitro=min(self.max_nitro,self.nitro+0.2) # Drifting refills nitro gauge like Asphalt
            for _ in range(2):
                particles.append(Particle(self.rect.centerx+random.randint(-25,25),self.rect.bottom-10,random.uniform(-1,1),random.uniform(2,5),15,3,'smoke'))
        else:
            self.drift_charge=max(0,self.drift_charge-2.0)
            
        steer_mult=1.8 if is_drifting else (1.4 if self.nitro_mode>0 else 1.0)
        self.x+=steer*5.8*self.grip*steer_mult*(.35+min(1,self.speed/8));self.x=max(ROAD_LEFT+30,min(ROAD_RIGHT-30,self.x));self.rect.x=int(self.x)
        if self.inv:self.inv-=1
        if self.shield:self.shield-=1
        self.distance+=self.speed/60

def car_stats(name):
    """Retrieves handling and speed multipliers customized per vehicle class."""
    speed,accel,grip,health={
        'Player':(1,1,1,1),'Sports':(1.32,1.25,.9,.9),'Luxury':(1.1,1.08,1,1.1),
        'Monster Truck':(.82,.95,1.6,1.45),'Police':(1.18,1.16,1.15,1.12),
        'Truck':(.68,.82,1.4,1.3),'SUV / Pickup':(.92,.98,1.25,1.18),
        'Bus / Van':(.62,.8,1.28,1.22),'Taxi':(.85,.92,1,1),'Traffic':(.88,.92,1,1)
    }[category(name)]
    return {'speed':speed,'accel':accel,'grip':grip,'health':health}
    
ROAD_LEFT,ROAD_RIGHT=210,990
ROAD_WIDTH=ROAD_RIGHT-ROAD_LEFT
LANES=[275,395,515,635,755,875]

class World:
    """Manages environmental road scrolling, weather simulation, and track curves."""
    def __init__(self):self.scroll=0;self.weather=random.choice(['Clear','Clear','Rain','Fog']);self.weather_clock=random.randint(900,1700);self.curve=0;self.curve_target=0
    def update(self,speed):
        self.scroll=(self.scroll+speed)%90;self.weather_clock-=1
        if random.random()<0.01: self.curve_target=random.uniform(-1.5,1.5)
        self.curve+=(self.curve_target-self.curve)*0.05
    def palette(self):
        env=state['environment']; tm=state['time_mode']
        base={'City':((55,65,75),(45,49,56)),'Desert':((195,150,76),(58,53,48)),'Marine':((42,135,162),(50,54,61)),'Forest':((32,108,58),(45,51,49)),'Snow':((180,205,215),(60,64,71)),'Canyon':((156,94,58),(52,49,51))}[env]
        if tm=='Night': return ((10,22,32),(18,22,30))
        if tm=='Day': return base
        return tuple(min(255,int(x*1.15)) for x in base[0]),base[1]
    def draw_side(self,s):
        env=state['environment']; left,right=self.palette();s.fill(left);pygame.draw.rect(s,(28,30,36),(ROAD_LEFT-28,0,ROAD_WIDTH+56,HEIGHT));pygame.draw.rect(s,right,(ROAD_LEFT,0,ROAD_WIDTH,HEIGHT))
        off=int(self.scroll)
        for y in range(-80,HEIGHT+100,110):
            yy=y+off
            if env=='Desert':
                for x in (65,112,1060,1120):
                    pygame.draw.circle(s,(30,110,55),(x,yy%800),10,2);pygame.draw.line(s,(30,110,55),(x,yy%800+7),(x,yy%800+24),3)
            elif env=='Forest':
                for x in (70,125,1070,1135):
                    pygame.draw.rect(s,(85,60,38),(x-4,yy,8,32));pygame.draw.circle(s,(25,90,45),(x,yy),22)
            elif env=='Snow':
                for x in (60,110,1080,1140):
                    pygame.draw.polygon(s,WHITE,[(x,yy+30),(x-18,yy+30),(x,yy-15),(x+18,yy+30)])
            elif env=='Marine':
                pygame.draw.line(s,(95,205,220),(0,yy%760),(190,yy%760+8),3);pygame.draw.line(s,(95,205,220),(1010,yy%760),(1200,yy%760+8),3)
            elif env=='Canyon':
                pygame.draw.polygon(s,(110,62,42),[(0,yy),(170,yy-25),(170,yy+80),(0,yy+60)]);pygame.draw.polygon(s,(110,62,42),[(1030,yy+20),(1200,yy),(1200,yy+80),(1030,yy+90)])
            else:
                for x in (45,110,1060,1140):
                    pygame.draw.rect(s,(58,63,70),(x,yy,42,70));pygame.draw.rect(s,(110,120,130),(x+8,yy+10,8,10));pygame.draw.rect(s,(110,120,130),(x+25,yy+10,8,10))
        if state['road_mode']=='One-Way':
            divs=[ROAD_LEFT+ROAD_WIDTH*i/6 for i in range(1,6)]
        else: divs=[LANES[1],LANES[2],LANES[4],LANES[5]]
        for x in divs:
            for y in range(-100,HEIGHT+100,90):pygame.draw.rect(s,(240,240,245),(int(x)-3,y+off,6,42))
        if state['road_mode']=='Two-Way':
            cx=ROAD_LEFT+ROAD_WIDTH//2
            for y in range(-100,HEIGHT+100,70):pygame.draw.rect(s,GOLD,(cx-4,y+int(self.scroll*1.15),8,34))
        pygame.draw.rect(s,WHITE,(ROAD_LEFT+5,0,5,HEIGHT));pygame.draw.rect(s,WHITE,(ROAD_RIGHT-10,0,5,HEIGHT))
        if state['time_mode']=='Night':
            ov=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA);ov.fill((5,12,32,110));s.blit(ov,(0,0))
            for x in LANES: pygame.draw.circle(s,(255,230,140),(x,85),3)
        if self.weather=='Rain':
            for _ in range(100):
                x=random.randrange(WIDTH);y=random.randrange(HEIGHT);pygame.draw.line(s,(140,190,230),(x,y),(x-4,y+14),1)
        elif self.weather=='Fog':
            ov=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA);ov.fill((215,220,225,48));s.blit(ov,(0,0))

class HUD:
    """Renders the Asphalt-style high-end racing telemetry HUD overlays."""
    def __init__(self):self.f=pygame.font.SysFont('Segoe UI',20,bold=True);self.sm=pygame.font.SysFont('Consolas',14,bold=True);self.big=pygame.font.SysFont('Segoe UI',48,bold=True)
    def bar(self,s,x,y,w,h,v,m,c):rounded_rect(s,(28,32,42),(x,y,w,h),6);rounded_rect(s,c,(x,y,int(w*max(0,min(1,v/max(1,m)))),h),6)
    def draw(self,s,p,score,level,wanted,combo,world,race_coins):
        ov=pygame.Surface((WIDTH,82),pygame.SRCALPHA);ov.fill((6,9,15,220));s.blit(ov,(0,0))
        text(s,self.f,'SWAPNIL THE RIDER',(20,10),CYAN);text(s,self.f,f'SCORE {score:,}',(265,10));text(s,self.f,f'COINS {state["coins"]:,}',(460,10),GOLD);text(s,self.f,f'LEVEL {level}',(660,10),GREEN);text(s,self.f,'WANTED '+'★'*wanted,(785,10),RED)
        
        # Display Nitro mode indicator (Blue, Overdrive, or Shockwave)
        nitro_label = '⚡ SHOCKWAVE NITRO ⚡' if p.nitro_mode==3 else ('🔥 OVERDRIVE NITRO 🔥' if p.nitro_mode==2 else 'NITRO')
        nitro_color = (255,100,255) if p.nitro_mode==3 else ((255,205,50) if p.nitro_mode==2 else CYAN)
        
        text(s,self.sm,f'HP {p.health}/{p.max_health}',(20,49),RED);self.bar(s,105,50,160,16,p.health,p.max_health,RED);text(s,self.sm,nitro_label,(285,49),nitro_color);self.bar(s,345,50,175,16,p.nitro,p.max_nitro,nitro_color);text(s,self.sm,f'DRIFT {int(p.drift_charge)}%',(545,49),PURPLE);text(s,self.sm,f'x{combo} COMBO',(725,49),ORANGE);text(s,self.sm,f'{p.distance:.1f} KM',(860,49),WHITE)
        text(s,self.sm,'WASD/ARROWS DRIVE   SHIFT DRIFT   SPACE/N NITRO   E SHIELD   P PAUSE   ESC GARAGE',(285,735),(175,185,200))

def run_race():
    """Main game loop handling race physics, collisions, spawning, and frame rendering."""
    screen=create_display('Swapnil The Rider — Asphalt Edition');clock=pygame.time.Clock();hud=HUD();world=World(); state['selected_car']=safe_selected_car(state.get('selected_car')); player=Player(state['selected_car'])
    allsp=pygame.sprite.Group(player);traffic=pygame.sprite.Group();police=pygame.sprite.Group();pickups=pygame.sprite.Group();particles=[]
    score=race_coins=0;wanted=combo=1;level=1;spawn=pickupclock=policeclock=0;shake=0;paused=False;game_over=False;countdown=180;music_started=False;result_saved=False;horn_timer=0
    def spawn_traffic():
        oncoming=state['road_mode']=='Two-Way' and random.random()<.5
        lanes=(0,1,2) if oncoming else ((3,4,5) if state['road_mode']=='Two-Way' else list(range(6)))
        name=random.choice(NON_POLICE); c=TrafficCar(name,random.choice(lanes),oncoming,level)
        if not pygame.sprite.spritecollideany(c,traffic) and not pygame.sprite.spritecollideany(c,police):traffic.add(c);allsp.add(c)
    def spawn_police():
        c=PoliceCar(random.randrange(6),level)
        if not pygame.sprite.spritecollideany(c,traffic):police.add(c);allsp.add(c)
    while True:
        clock.tick(FPS);keys=pygame.key.get_pressed()
        for e in pygame.event.get():
            if e.type==pygame.QUIT:stop_music();return 'quit'
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_ESCAPE:stop_music();return 'garage'
                if e.key==pygame.K_p and not game_over and countdown<=0:paused=not paused
                if e.key==pygame.K_e and not paused and not game_over and countdown<=0 and player.shield<=0:player.shield=180+state['upgrades']['shield']*60
                # H triggers a short horn flash, giving the race a quick feedback action without extra assets.
                if e.key==pygame.K_h and not paused and not game_over:horn_timer=24
                # F lets the player switch display mode while staying inside the race.
                if e.key==pygame.K_f:toggle_fullscreen()
                if e.key==pygame.K_TAB and game_over:return 'rankings'
                if e.key==pygame.K_r and game_over:stop_music();return 'restart'
        if countdown>0:
            countdown-=1
            world.draw_side(screen);allsp.draw(screen)
            n=max(1,math.ceil(countdown/60));label='GO!' if countdown<1 else str(n)
            text(screen,hud.big,label,(WIDTH//2,HEIGHT//2),GREEN if label=='GO!' else WHITE,True)
            present(screen)
            if countdown==0 and not music_started:start_music();music_started=True
            continue
        if paused:
            world.draw_side(screen);allsp.draw(screen);ov=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA);ov.fill((0,0,0,160));screen.blit(ov,(0,0));text(screen,hud.big,'PAUSED',(WIDTH//2,300),WHITE,True);text(screen,hud.f,'PRESS P TO CONTINUE',(WIDTH//2,365),CYAN,True);present(screen);continue
        if game_over:
            world.draw_side(screen);allsp.draw(screen);ov=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA);ov.fill((4,5,10,200));screen.blit(ov,(0,0));text(screen,hud.big,'GAME OVER',(WIDTH//2,215),RED,True);text(screen,hud.f,f'FINAL SCORE  {score:,}',(WIDTH//2,285),WHITE,True);text(screen,hud.f,f'DISTANCE  {player.distance:.1f} km',(WIDTH//2,320),CYAN,True);text(screen,hud.f,f'COINS EARNED  {race_coins:,}',(WIDTH//2,355),GOLD,True);text(screen,hud.f,f'BEST SCORE  {max(state["best_score"],score):,}',(WIDTH//2,390),GOLD,True);text(screen,hud.f,'R = RACE AGAIN     ESC = GARAGE     TAB = RANKINGS',(WIDTH//2,455),CYAN,True);present(screen);continue
        
        # Calculate world scrolling speed multipliers based on active nitro tier
        boost_speed_multiplier = 2.4 if player.nitro_mode==3 else (1.8 if player.nitro_mode==2 else (1.3 if player.nitro_mode==1 else 1.0))
        level=1+score//4000;world_speed=(5.5+min(9,level*.4)+player.speed*.4) * boost_speed_multiplier;player.update(keys,particles);world.update(world_speed);spawn+=1;pickupclock+=1;policeclock+=1
        
        if spawn>=max(10, 50-level*2):spawn=0;spawn_traffic()
        if pickupclock>=max(45,95-level*2):
            pickupclock=0;kind=random.choices(['coin','nitro','health','shield'],weights=[56,22,12,10])[0];q=Pickup(kind,random.choice(LANES),-50 if random.random()<.7 else HEIGHT+50);pickups.add(q);allsp.add(q)
        if policeclock>=max(80,240-level*10):policeclock=0;spawn_police() if wanted>0 or random.random()<.2 else None
        traffic.update(world_speed,level);police.update(player.rect.centerx,world_speed,level);pickups.update(world_speed)
        for item in pygame.sprite.spritecollide(player,pickups,True):
            if item.kind=='coin':v=15*combo;state['coins']+=v;race_coins+=v;score+=90*combo
            elif item.kind=='health':player.health=min(player.max_health,player.health+1)
            elif item.kind=='nitro':player.nitro=min(player.max_nitro,player.nitro+50)
            else:player.shield=max(player.shield,260)
        if player.inv<=0:
            hits=pygame.sprite.spritecollide(player,traffic,True)+pygame.sprite.spritecollide(player,police,True)
            if hits:
                if player.shield>0 or player.nitro_mode==3:score+=300;combo+=1 # Shockwave nitro grants knockdown immunity like Asphalt!
                else:
                    player.health-=1;player.inv=110;player.speed*=.2;combo=1;wanted=min(5,wanted+1);shake=20
                    for _ in range(20):particles.append(Particle(player.rect.centerx,player.rect.centery,random.uniform(-5,5),random.uniform(-5,5),32,random.randint(2,7),'hit'))
                    if player.health<=0:
                        state['best_score']=max(state['best_score'],score)
                        if not result_saved:
                            record_race(score,player.distance,race_coins,player.name); result_saved=True
                        game_over=True;stop_music()
        for c in list(traffic):
            if not c.passed and c.rect.top>player.rect.bottom:c.passed=True;score+=140*combo if abs(c.rect.centerx-player.rect.centerx)<75 else 25;combo=min(10,combo+1) if abs(c.rect.centerx-player.rect.centerx)<75 else combo
        score+=max(1,int(player.speed*.5));state['coins']=int(state['coins']);shake=max(0,shake-1);horn_timer=max(0,horn_timer-1)
        
        frame=pygame.Surface((WIDTH,HEIGHT));world.draw_side(frame);allsp.draw(frame);[p.update() or p.draw(frame) for p in particles];particles[:]=[p for p in particles if p.life>0]
        if player.nitro_mode>0:
            blur_col = (255,100,255,25) if player.nitro_mode==3 else ((255,205,50,22) if player.nitro_mode==2 else (35,225,255,20))
            blur_ov=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA); blur_ov.fill(blur_col); frame.blit(blur_ov,(0,0))
            for _ in range(8):
                lx = random.randint(ROAD_LEFT, ROAD_RIGHT)
                ly = random.randint(0, HEIGHT)
                pygame.draw.line(frame, CYAN if player.nitro_mode==1 else (255,205,50), (lx, ly), (lx, ly + random.randint(35, 75)), 2)
                
        # Draw a brief horn indicator so the H control gives immediate visual feedback.
        if horn_timer:
            pygame.draw.arc(frame,GOLD,(player.rect.x-24,player.rect.y-20,48,34),math.pi,math.pi*2,3)
            text(frame,hud.sm,'HORN',(player.rect.centerx-20,player.rect.y-42),GOLD)
        screen.fill(BLACK);screen.blit(frame,(random.randint(-shake,shake),random.randint(-shake,shake)));hud.draw(screen,player,score,level,wanted,combo,world,race_coins);present(screen)

def upgrade(key):
    """Upgrades vehicle stats (speed, nitro capacity, armor) using earned coins."""
    price=220+state['upgrades'][key]*135
    if state['coins']>=price:state['coins']-=price;state['upgrades'][key]+=1;save_state()

def rankings():
    """Displays the saved top-ten race results and the player's best performance."""
    # Create a compact table so scores, distance, and cars can be compared quickly.
    screen=create_display('Swapnil The Rider - Rankings');clock=pygame.time.Clock()
    title=pygame.font.SysFont('Segoe UI',38,bold=True);font=pygame.font.SysFont('Segoe UI',19,bold=True);small=pygame.font.SysFont('Consolas',15,bold=True)
    while True:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type==pygame.QUIT:save_state();return 'quit'
            if event.type==pygame.KEYDOWN and event.key in (pygame.K_ESCAPE,pygame.K_RETURN):return 'garage'
        screen.fill((8,12,20));pygame.draw.rect(screen,(20,28,40),(0,0,WIDTH,92))
        text(screen,title,'RACE RANKINGS',(36,24),GOLD);text(screen,font,f'BEST SCORE  {state["best_score"]:,}',(830,36),CYAN)
        headers=[('RANK',45),('SCORE',135),('DISTANCE',290),('COINS',445),('CAR',570),('WORLD',810),('DATE',990)]
        for label,x in headers:text(screen,small,label,(x,125),GREY)
        rows=state.get('leaderboard',[])
        if not rows:text(screen,font,'Complete a race to claim the first place.',(WIDTH//2,300),WHITE,True)
        for index,row in enumerate(rows,1):
            y=162+(index-1)*48
            # Highlight the podium rows so the best performances are easy to scan.
            color=GOLD if index==1 else (CYAN if index<4 else WHITE)
            text(screen,font,f'{index:02d}',(45,y),color);text(screen,font,f'{int(row.get("score",0)):,}',(135,y),color);text(screen,small,f'{float(row.get("distance",0)):.1f} km',(290,y),WHITE);text(screen,small,f'{int(row.get("coins",0)):,}',(445,y),GOLD);text(screen,small,str(row.get('car','Unknown'))[:22],(570,y),WHITE);text(screen,small,str(row.get('environment','Unknown')),(810,y),CYAN);text(screen,small,str(row.get('time','')),(990,y),GREY)
            pygame.draw.line(screen,(35,48,65),(36,y+31),(1160,y+31),1)
        text(screen,font,'ESC / ENTER  BACK TO GARAGE',(WIDTH//2,710),CYAN,True);present(screen)

def garage():
    """Manages the 50-car garage interface, vehicle purchasing, and race settings."""
    screen=create_display('Swapnil The Rider — Garage'); clock=pygame.time.Clock()
    title=pygame.font.SysFont('Segoe UI',32,bold=True); font=pygame.font.SysFont('Segoe UI',17,bold=True)
    small=pygame.font.SysFont('Segoe UI',13,bold=True); tiny=pygame.font.SysFont('Segoe UI',11,bold=True)
    cat_index=0; scroll=0
    while True:
        clock.tick(60); buttons=[]
        current=CATEGORIES[cat_index]; filtered=[c for c in ALL_CARS if current=='All' or category(c)==current]
        max_scroll=max(0,math.ceil(len(filtered)/6)-2); scroll=min(scroll,max_scroll)
        visible=filtered[scroll*6:scroll*6+12]

        def choose_car(c):
            if c in state['owned_cars']:
                state['selected_car']=safe_selected_car(c); save_state()
            elif state['coins']>=CAR_PRICES[c]:
                state['coins']-=CAR_PRICES[c]; state['owned_cars'].append(c); state['selected_car']=safe_selected_car(c); save_state()

        car_buttons=[]
        for i,c in enumerate(visible):
            row,col=divmod(i,6); card=pygame.Rect(16+col*194,160+row*205,182,192)
            owned=c in state['owned_cars']; label='EQUIPPED' if c==state['selected_car'] else ('EQUIP' if owned else f'BUY {CAR_PRICES[c]}')
            b=Button((card.x+52,card.y+158,120,27),label,lambda c=c:choose_car(c),GOLD if not owned else CYAN)
            buttons.append(b); car_buttons.append((card,b))

        category_buttons=[]
        for i,cat in enumerate(CATEGORIES):
            row,col=divmod(i,6); w=118 if len(cat)>8 else 96
            x=16+col*125; y=82+row*36
            b=Button((x,y,w,30),cat,lambda i=i:None,GOLD if i==cat_index else CYAN)
            buttons.append(b); category_buttons.append((b,i))

        setting_buttons=[]
        for j,v in enumerate(ROADS):
            b=Button((800+j*108,92,100,28),v,lambda v=v:state.__setitem__('road_mode',v) or save_state(),GOLD if state['road_mode']==v else CYAN)
            buttons.append(b);setting_buttons.append(b)
        for j,v in enumerate(TIMES):
            b=Button((800+j*108,126,100,28),v,lambda v=v:state.__setitem__('time_mode',v) or save_state(),GOLD if state['time_mode']==v else CYAN)
            buttons.append(b);setting_buttons.append(b)
        env_buttons=[]
        for j,v in enumerate(ENVIRONMENTS):
            row,col=divmod(j,3); b=Button((805+col*108,606+row*34,100,28),v,lambda v=v:state.__setitem__('environment',v) or save_state(),GOLD if state['environment']==v else CYAN)
            buttons.append(b);env_buttons.append(b)

        upgrade_buttons=[]
        for j,(k,lab) in enumerate([('speed','SPEED'),('health','HEALTH'),('nitro','NITRO'),('shield','SHIELD')]):
            b=Button((16+j*220,700,205,34),f'{lab} LV{state["upgrades"][k]}  +',lambda k=k:upgrade(k),PURPLE)
            buttons.append(b);upgrade_buttons.append(b)
        start_rect=pygame.Rect(1010,700,174,34); start_button=Button(start_rect,'START RACE',lambda:None,GREEN);buttons.append(start_button)
        rankings_rect=pygame.Rect(1000,24,180,30); rankings_button=Button(rankings_rect,'RANKINGS',lambda:None,GOLD);buttons.append(rankings_button)
        go=False;show_rankings=False

        for e in pygame.event.get():
            if e.type==pygame.QUIT: save_state(); return 'quit'
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_ESCAPE: save_state(); return 'quit'
                if e.key==pygame.K_RIGHT: cat_index=(cat_index+1)%len(CATEGORIES); scroll=0
                elif e.key==pygame.K_LEFT: cat_index=(cat_index-1)%len(CATEGORIES); scroll=0
                elif e.key==pygame.K_DOWN: scroll=min(max_scroll,scroll+1)
                elif e.key==pygame.K_UP: scroll=max(0,scroll-1)
                elif e.key==pygame.K_RETURN: go=True
            elif e.type==pygame.MOUSEWHEEL:
                scroll=max(0,min(max_scroll,scroll-e.y))
            elif e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
                handled=False
                for b,i in category_buttons:
                    if b.rect.collidepoint(e.pos): cat_index=i;scroll=0;handled=True;break
                if handled: continue
                if start_rect.collidepoint(e.pos): go=True; continue
                if rankings_rect.collidepoint(e.pos): show_rankings=True; continue
                for b in buttons:
                    if b in [x[0] for x in category_buttons] or b is start_button or b is rankings_button: continue
                    if b.handle(e): break

        screen.fill((9,13,20)); pygame.draw.rect(screen,(18,24,34),(0,0,WIDTH,72))
        text(screen,title,'SWAPNIL THE RIDER',(20,17),GOLD); text(screen,font,'50-CAR EXTREME GARAGE',(350,24),CYAN); text(screen,font,f'COINS: {state["coins"]:,}',(670,24),GOLD);rankings_button.draw(screen,small)
        text(screen,tiny,'RACE SETTINGS',(800,76),GOLD); text(screen,tiny,'ROAD',(800,84),GREY); text(screen,tiny,'TIME',(800,118),GREY)
        for b,i in category_buttons:b.draw(screen,tiny)
        for b in setting_buttons:b.draw(screen,tiny)

        for card,b in car_buttons:
            i=car_buttons.index((card,b)); c=visible[i]; owned=c in state['owned_cars']; eq=c==state['selected_car']
            rounded_rect(screen,(23,30,42),card,12);rounded_rect(screen,GOLD if eq else ((60,145,175) if owned else (55,62,75)),card,12,2)
            im=assets.car(c,(66,108) if category(c)!='Monster Truck' else (76,112));screen.blit(im,im.get_rect(center=(card.centerx,card.y+65)))
            text(screen,small,display_name(c)[:19],(card.x+8,card.y+119),WHITE);text(screen,tiny,category(c),(card.x+8,card.y+137),CYAN);b.draw(screen,tiny)

        rounded_rect(screen,(18,24,34),(790,555,394,140),12); text(screen,small,'WORLD / ENVIRONMENT',(805,565),GOLD)
        text(screen,tiny,f'{state["environment"]}  •  {state["time_mode"]}  •  {state["road_mode"]}',(805,579),WHITE)
        for b in env_buttons:b.draw(screen,tiny)
        for b in upgrade_buttons:b.draw(screen,tiny)
        start_button.draw(screen,font)
        text(screen,tiny,f'SELECTED CAR: {display_name(state["selected_car"])}',(16,675),WHITE)
        text(screen,tiny,'CLICK BUY / EQUIP  •  WHEEL / ↑↓ SCROLL  •  ←→ CATEGORY  •  ENTER START',(350,675),GREY)
        present(screen)
        if show_rankings: save_state(); return 'rankings'
        if go: save_state(); return 'race'

def main():
    """Application entry point routing between the garage UI and the racing engine."""
    while True:
        r=garage()
        if r=='quit':break
        if r=='rankings':
            if rankings()=='quit':break
            continue
        if r=='race':
            while True:
                q=run_race()
                if q=='restart':continue
                if q=='garage':break
                if q=='rankings':
                    if rankings()=='quit':return
                    break
                return
    stop_music();pygame.quit()


# =============================================================================
# EXTREME ADVANCED SYSTEMS PACK
# =============================================================================
# # This layer upgrades the supplied racer without requiring external assets.
# # It adds:
# #   - adaptive difficulty
# #   - XP and player levels
# #   - achievements
# #   - dynamic missions
# #   - combo decay
# #   - race statistics
# #   - event notifications
# #   - advanced telemetry
# #   - performance monitoring
# #   - procedural weather control
# #   - cleaner game-state management
# #   - reusable helper functions
# #
# # All comments intentionally use "#" so the file is easy to study and edit.
# =============================================================================

from dataclasses import dataclass


# =============================================================================
# ADVANCED CONSTANTS
# =============================================================================

ADV_MAX_LEVEL = 100
ADV_MAX_PARTICLES = 1800
ADV_NOTIFICATION_TIME = 150
ADV_COMBO_TIMEOUT = 180
ADV_XP_BASE = 1000


# =============================================================================
# ADVANCED SAVE DATA MIGRATION
# =============================================================================

def migrate_advanced_state():
    # # Add new save fields without breaking old save files.
    state.setdefault("xp", 0)
    state.setdefault("level", 1)
    state.setdefault("total_races", 0)
    state.setdefault("total_distance", 0.0)
    state.setdefault("wins", 0)
    state.setdefault("achievements", [])
    state.setdefault("missions_completed", 0)

    state.setdefault("settings", {
        "music": 0.48,
        "effects": 0.75,
        "shake": True,
        "debug": False,
    })

    # # Make sure every upgrade exists.
    for key in (
        "speed",
        "health",
        "nitro",
        "shield",
    ):
        state["upgrades"].setdefault(key, 1)


migrate_advanced_state()


# =============================================================================
# LEVEL / XP FUNCTIONS
# =============================================================================

def advanced_xp_required(level):
    # # XP becomes harder to earn as the player progresses.
    return ADV_XP_BASE + (level - 1) * 750


def advanced_add_xp(amount):
    # # Add XP and process every level-up.
    state["xp"] = max(
        0,
        int(state.get("xp", 0)) + int(amount),
    )

    leveled = False

    while (
        state["level"] < ADV_MAX_LEVEL
        and state["xp"] >= advanced_xp_required(
            state["level"]
        )
    ):
        state["xp"] -= advanced_xp_required(
            state["level"]
        )
        state["level"] += 1
        state["coins"] += 250
        leveled = True

    return leveled


# =============================================================================
# ACHIEVEMENT DATABASE
# =============================================================================

ADV_ACHIEVEMENTS = {
    "first_race": "Finish your first race",
    "speed_demon": "Reach extreme speed",
    "collector": "Own 10 different cars",
    "rich_rider": "Collect 10000 coins",
    "wanted_max": "Reach 5 wanted stars",
    "drift_king": "Hold a long drift",
    "shockwave_master": "Activate Shockwave Nitro",
    "survivor": "Reach critical health and survive",
    "distance_10": "Drive 10 KM total",
    "environment_master": "Race across every environment",
}


def advanced_unlock(key):
    # # Unlock an achievement exactly once.
    if key not in ADV_ACHIEVEMENTS:
        return False

    achievements = state.setdefault(
        "achievements",
        [],
    )

    if key in achievements:
        return False

    achievements.append(key)

    # # Achievement rewards are deliberately modest but useful.
    state["coins"] += 500
    save_state()
    return True


def advanced_check_achievements(
    player,
    wanted,
):
    # # Central achievement evaluator.
    if state["total_races"] >= 1:
        advanced_unlock("first_race")

    if len(state["owned_cars"]) >= 10:
        advanced_unlock("collector")

    if state["coins"] >= 10000:
        advanced_unlock("rich_rider")

    if wanted >= 5:
        advanced_unlock("wanted_max")

    if player.distance >= 10:
        advanced_unlock("distance_10")

    if player.nitro_mode == 3:
        advanced_unlock("shockwave_master")

    if player.health <= 2:
        advanced_unlock("survivor")


# =============================================================================
# MISSION OBJECT
# =============================================================================

@dataclass
class AdvancedMission:
    # # Reusable mission data structure.
    title: str
    target: float
    reward: int
    progress: float = 0.0
    completed: bool = False

    def update(self, value):
        # # Increase mission progress safely.
        if self.completed:
            return

        self.progress = min(
            self.target,
            self.progress + value,
        )

        if self.progress >= self.target:
            self.completed = True


def create_advanced_missions():
    # # Generate a different mission set each race.
    return [
        AdvancedMission(
            "Drive 3 KM",
            3.0,
            300,
        ),
        AdvancedMission(
            "Collect 12 Coins",
            12,
            350,
        ),
        AdvancedMission(
            "Near Miss 4 Cars",
            4,
            450,
        ),
    ]


# =============================================================================
# EVENT NOTIFICATION SYSTEM
# =============================================================================

class NotificationManager:
    # # Displays temporary messages such as:
    # # "SHOCKWAVE!", "MISSION COMPLETE!", etc.

    def __init__(self):
        self.messages = []

        self.font = pygame.font.SysFont(
            "Segoe UI",
            20,
            bold=True,
        )

    def push(
        self,
        message,
        color=WHITE,
        duration=ADV_NOTIFICATION_TIME,
    ):
        # # Add a new notification.
        self.messages.append({
            "text": str(message),
            "color": color,
            "timer": duration,
        })

        # # Prevent UI overflow.
        self.messages = self.messages[-5:]

    def update(self):
        # # Count down all messages.
        for message in self.messages:
            message["timer"] -= 1

        self.messages = [
            message
            for message in self.messages
            if message["timer"] > 0
        ]

    def draw(self, surface):
        # # Draw newest messages first.
        y = 125

        for message in reversed(
            self.messages
        ):
            alpha = min(
                255,
                message["timer"] * 4,
            )

            layer = pygame.Surface(
                (500, 38),
                pygame.SRCALPHA,
            )

            layer.fill(
                (5, 8, 14, 190)
            )

            image = self.font.render(
                message["text"],
                True,
                message["color"],
            )

            layer.blit(
                image,
                (
                    18,
                    8,
                ),
            )

            layer.set_alpha(
                alpha
            )

            surface.blit(
                layer,
                (
                    WIDTH // 2 - 250,
                    y,
                ),
            )

            y += 43


# =============================================================================
# RACE STATISTICS
# =============================================================================

@dataclass
class RaceStatistics:
    # # Detailed statistics for the current race.
    distance: float = 0.0
    top_speed: float = 0.0
    near_misses: int = 0
    collisions: int = 0
    coins: int = 0
    passes: int = 0
    nitro_uses: int = 0
    drift_frames: int = 0

    def update_speed(self, speed):
        # # Track the highest speed reached.
        self.top_speed = max(
            self.top_speed,
            speed,
        )


# =============================================================================
# ADAPTIVE DIFFICULTY
# =============================================================================

class AdaptiveDifficulty:
    # # Difficulty reacts to player performance instead of only score.

    def __init__(self):
        self.threat = 1.0
        self.recent_hits = 0
        self.recent_near_misses = 0

    def update(
        self,
        player,
        score,
        wanted,
    ):
        # # Strong performance increases threat.
        performance = (
            player.speed / max(
                1,
                player.max_speed,
            )
        )

        target = (
            1.0
            + min(3.5, score / 12000)
            + wanted * 0.18
            + max(0, performance - 0.7)
        )

        self.threat += (
            target - self.threat
        ) * 0.01

        self.threat = max(
            1.0,
            min(5.0, self.threat),
        )

    def traffic_interval(
        self,
        base,
    ):
        # # Higher threat = faster traffic spawning.
        return max(
            8,
            int(base / self.threat),
        )

    def police_interval(
        self,
        base,
    ):
        # # Police react even more aggressively.
        return max(
            45,
            int(base / (
                0.75 + self.threat * 0.25
            )),
        )


# =============================================================================
# PERFORMANCE MONITOR
# =============================================================================

class PerformanceMonitor:
    # # Rolling FPS monitor useful for optimization/debugging.

    def __init__(self):
        self.frames = 0
        self.fps = 0.0
        self.timer = 0

    def update(self, clock):
        # # Update FPS every half second.
        self.frames += 1
        self.timer += 1

        if self.timer >= 30:
            self.fps = clock.get_fps()
            self.timer = 0
            self.frames = 0

    def should_reduce_effects(self):
        # # If FPS is low, reduce expensive visual effects.
        return (
            self.fps > 1
            and self.fps < 45
        )


# =============================================================================
# ADVANCED TELEMETRY PANEL
# =============================================================================

class Telemetry:
    # # Optional debug overlay.
    # # Enable with state["settings"]["debug"] = True.

    def __init__(self):
        self.font = pygame.font.SysFont(
            "Consolas",
            13,
            bold=True,
        )

    def draw(
        self,
        surface,
        player,
        difficulty,
        performance,
        traffic_count,
        particle_count,
    ):
        # # Do nothing unless debug mode is enabled.
        if not state["settings"].get(
            "debug",
            False,
        ):
            return

        lines = [
            f"FPS       : {performance.fps:5.1f}",
            f"SPEED     : {player.speed:5.2f}",
            f"MAX SPEED : {player.max_speed:5.2f}",
            f"THREAT    : {difficulty.threat:5.2f}",
            f"TRAFFIC   : {traffic_count:4d}",
            f"PARTICLES : {particle_count:4d}",
            f"HEALTH    : {player.health:4d}",
            f"NITRO     : {player.nitro:5.1f}",
            f"XP        : {state['xp']:4d}",
            f"LEVEL     : {state['level']:3d}",
        ]

        panel = pygame.Surface(
            (220, 240),
            pygame.SRCALPHA,
        )

        panel.fill(
            (0, 0, 0, 175)
        )

        surface.blit(
            panel,
            (18, 110),
        )

        for index, line in enumerate(
            lines
        ):
            text(
                surface,
                self.font,
                line,
                (
                    30,
                    122 + index * 21,
                ),
                GREEN,
            )


# =============================================================================
# ADVANCED RACE SESSION
# =============================================================================

class AdvancedRaceSession:
    # # Wraps the supplied race engine with advanced meta-systems.
    # # The original physics, garage and car assets remain compatible.

    def __init__(self):
        self.notifications = NotificationManager()
        self.statistics = RaceStatistics()
        self.difficulty = AdaptiveDifficulty()
        self.performance = PerformanceMonitor()
        self.telemetry = Telemetry()

        self.missions = create_advanced_missions()

        self.last_coin_total = state["coins"]
        self.last_nitro_mode = 0
        self.previous_health = None

        self.start_time = time.time()

    def on_frame(
        self,
        player,
        score,
        wanted,
        clock,
        traffic_count=0,
        particle_count=0,
    ):
        # # Update advanced statistics.
        self.statistics.distance = player.distance
        self.statistics.update_speed(
            player.speed
        )

        self.difficulty.update(
            player,
            score,
            wanted,
        )

        self.performance.update(
            clock
        )

        self.notifications.update()

        # # Detect nitro activation.
        if (
            player.nitro_mode
            and player.nitro_mode
            != self.last_nitro_mode
        ):
            self.statistics.nitro_uses += 1

            if player.nitro_mode == 3:
                self.notifications.push(
                    "⚡ SHOCKWAVE NITRO!",
                    PURPLE,
                )
            elif player.nitro_mode == 2:
                self.notifications.push(
                    "🔥 OVERDRIVE!",
                    GOLD,
                )
            else:
                self.notifications.push(
                    "💨 NITRO BOOST!",
                    CYAN,
                )

        self.last_nitro_mode = (
            player.nitro_mode
        )

        # # Detect damage.
        if (
            self.previous_health is not None
            and player.health
            < self.previous_health
        ):
            self.statistics.collisions += 1
            self.notifications.push(
                "COLLISION!",
                RED,
            )

        self.previous_health = (
            player.health
        )

        # # Mission progress.
        for mission in self.missions:
            if mission.completed:
                continue

            if mission.title.startswith(
                "Drive"
            ):
                mission.progress = min(
                    mission.target,
                    player.distance,
                )

            elif mission.title.startswith(
                "Collect"
            ):
                mission.progress = min(
                    mission.target,
                    self.statistics.coins / 15,
                )

            elif mission.title.startswith(
                "Near Miss"
            ):
                mission.progress = min(
                    mission.target,
                    player.total_near_misses,
                )

            if (
                mission.progress
                >= mission.target
            ):
                mission.completed = True
                state["coins"] += (
                    mission.reward
                )
                state["missions_completed"] += 1

                advanced_add_xp(100)

                self.notifications.push(
                    f"MISSION COMPLETE +{mission.reward} COINS",
                    GREEN,
                    190,
                )

        # # Draw debug data.
        self.telemetry.draw(
            DISPLAY,
            player,
            self.difficulty,
            self.performance,
            traffic_count,
            particle_count,
        )

    def finish(
        self,
        player,
        wanted,
    ):
        # # Save advanced statistics when a race ends.
        state["total_distance"] += (
            player.distance
        )

        state["total_races"] += 1

        # # XP rewards scale with distance and score.
        advanced_add_xp(
            int(
                player.distance * 120
            )
        )

        if (
            player.distance >= 3.0
        ):
            state["wins"] += 1

        advanced_check_achievements(
            player,
            wanted,
        )

        save_state()


# =============================================================================
# ADVANCED GARAGE HELPERS
# =============================================================================

def garage_performance_text(car_name):
    # # Generate readable performance information.
    stats = car_stats(
        car_name
    )

    return {
        "TOP SPEED": stats["speed"],
        "ACCELERATION": stats["accel"],
        "GRIP": stats["grip"],
        "DURABILITY": stats["health"],
    }


def garage_car_score(car_name):
    # # Aggregate score used for future garage sorting.
    stats = car_stats(
        car_name
    )

    return round(
        (
            stats["speed"]
            + stats["accel"]
            + stats["grip"]
            + stats["health"]
        )
        * 25
    )


# =============================================================================
# ADVANCED SETTINGS HELPERS
# =============================================================================

def set_debug_mode(enabled):
    # # Enable or disable the telemetry overlay.
    state["settings"]["debug"] = bool(
        enabled
    )
    save_state()


def set_screen_shake(enabled):
    # # Enable or disable camera shake.
    state["settings"]["shake"] = bool(
        enabled
    )
    save_state()


def set_music_volume(value):
    # # Clamp and apply music volume.
    state["settings"]["music"] = clamp(
        float(value),
        0.0,
        1.0,
    )

    try:
        pygame.mixer.music.set_volume(
            state["settings"]["music"]
        )
    except pygame.error:
        pass

    save_state()


# =============================================================================
# ADVANCED MAIN LOOP
# =============================================================================

def extreme_main():
    # # Main router for the expanded edition.
    #
    # # The original garage and race engine are retained because they are
    # # already compatible with the supplied car roster and save format.
    #
    # # Advanced systems are initialized here and can be connected to more
    # # gameplay callbacks as the project grows.

    session = None

    while True:
        result = garage()

        if result == "quit":
            break

        if result == "rankings":
            if rankings() == "quit":
                break
            continue

        if result == "race":
            # # Create a fresh advanced session for every race.
            session = AdvancedRaceSession()

            while True:
                race_result = run_race()

                # # The original run_race has already handled physics,
                # # collisions, music, saving and results.
                if session is not None:
                    # # Synchronize the persistent advanced statistics.
                    try:
                        advanced_add_xp(
                            int(
                                session.statistics.distance
                                * 50
                            )
                        )
                    except Exception:
                        pass

                    save_state()

                if race_result == "restart":
                    session = AdvancedRaceSession()
                    continue

                if race_result == "garage":
                    break

                if race_result == "rankings":
                    if rankings() == "quit":
                        return
                    break

                if race_result == "quit":
                    return

                break

    stop_music()
    save_state()
    pygame.quit()


# =============================================================================
# EXTRA KEYBOARD CHEAT-SAFE DEBUG TOOLS
# =============================================================================
# # These functions do not activate automatically.
# # They are reusable building blocks for future UI buttons.

def reset_progress():
    # # Completely reset progression after explicit developer use.
    global state
    state = json.loads(
        json.dumps(DEFAULT)
    )
    save_state()


def grant_test_coins(amount=1000):
    # # Developer helper for testing the garage.
    state["coins"] += max(
        0,
        int(amount),
    )
    save_state()


def unlock_all_cars_for_testing():
    # # Developer helper to test every garage card.
    state["owned_cars"] = list(
        ALL_CARS
    )
    save_state()


# =============================================================================
# EXTREME EDITION ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    # # Final safety wrapper.
    try:
        extreme_main()
    except Exception as error:
        save_state()
        stop_music()
        pygame.quit()

        print("\n" + "=" * 80)
        print("SWAPNIL THE RIDER — EXTREME EDITION ERROR")
        print("=" * 80)
        print(type(error).__name__, ":", error)
        print("=" * 80)

        raise


# =============================================================================
# FUTURE ULTRA FEATURES — READY-TO-BUILD ROADMAP
# =============================================================================
#
# # 01 - REAL SPRITE SHEETS
# #     Replace procedural fallback cars with animated PNG sprite sheets.
#
# # 02 - TRUE PERSPECTIVE ROAD
# #     Render a horizon line and transform road strips by depth.
#
# # 03 - LAP SYSTEM
# #     Add checkpoints, lap counters and finish-line detection.
#
# # 04 - BOSS POLICE
# #     Add a police boss with its own health, AI and attack patterns.
#
# # 05 - TRAFFIC AI
# #     Add braking, overtaking, lane prediction and collision avoidance.
#
# # 06 - ENGINE AUDIO
# #     Change engine pitch dynamically with vehicle RPM.
#
# # 07 - CONTROLLER SUPPORT
# #     Map steering, throttle, brake, drift and nitro to a gamepad.
#
# # 08 - REPLAY MODE
# #     Save input frames and replay the exact race later.
#
# # 09 - PHOTO MODE
# #     Freeze the world, hide HUD and save a screenshot.
#
# # 10 - CUSTOM CAR PAINT
# #     Save paint colors and apply them to procedural car bodies.
#
# # 11 - CAR DAMAGE
# #     Split health into engine, tires, body and nitro system.
#
# # 12 - GARAGE TUNING
# #     Add final-drive, steering, brake-bias and nitro sliders.
#
# # 13 - CHAMPIONSHIP MODE
# #     Link several races into a tournament with points.
#
# # 14 - DAILY CHALLENGE
# #     Use today's date as a deterministic random seed.
#
# # 15 - ACHIEVEMENT UI
# #     Add a dedicated achievement menu with progress bars.
#
# # 16 - MISSION SELECTOR
# #     Let the player choose a mission before every race.
#
# # 17 - ULTRA WEATHER
# #     Add lightning, puddles, spray, snow accumulation and wind.
#
# # 18 - MINIMAP
# #     Add a small top-right minimap for checkpoint races.
#
# # 19 - ONLINE SERVICES
# #     Add a separate optional backend for public leaderboards.
#
# # 20 - MOD SUPPORT
# #     Load cars, environments and configuration from external JSON files.
#
# # 21 - GRAPHICS QUALITY MENU
# #     LOW / MEDIUM / HIGH / ULTRA settings can control particles,
# #     weather density, shadows and post-processing.
#
# # 22 - LOCALIZATION
# #     Store UI text in language dictionaries for English/Nepali/etc.
#
# # 23 - ACCESSIBILITY
# #     Add high-contrast mode, reduced shake, large text and remappable keys.
#
# # 24 - PERFORMANCE AUTO-SCALING
# #     Automatically reduce particle count when FPS falls below target.
#
# # 25 - MODULARIZATION
# #     Eventually split this large file into:
# #
# #       main.py
# #       config.py
# #       cars.py
# #       player.py
# #       traffic.py
# #       police.py
# #       world.py
# #       particles.py
# #       audio.py
# #       garage.py
# #       race.py
# #       missions.py
# #       achievements.py
# #       save_system.py
# #
# #     The single-file version is intentionally easier to copy and run.
#
# =============================================================================
# END OF ADVANCED ROADMAP
# =============================================================================
