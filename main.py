import pygame
import sys, os
import random
import time
from pygame import mixer

pygame.init()
pygame.font.init()

# Window set up
width = 750
height = 750
displaySurface = pygame.display.set_mode((width, height))
gameIcon = pygame.image.load(os.path.join('assets','ufo.png'))
pygame.display.set_icon(gameIcon)
pygame.display.set_caption("Space Invaders")

# Enemy Spaceships
blueSpaceship = pygame.image.load(os.path.join('assets', 'pixel_ship_blue_small.png'))
greenSpaceship = pygame.image.load(os.path.join('assets', 'pixel_ship_green_small.png'))
redSpaceship = pygame.image.load(os.path.join('assets', 'pixel_ship_red_small.png'))

# Enemy laser bullets
blueLaserBullet = pygame.image.load(os.path.join('assets', 'pixel_laser_blue.png'))
greenLaserBullet = pygame.image.load(os.path.join('assets', 'pixel_laser_green.png'))
redLaserBullet = pygame.image.load(os.path.join('assets', 'pixel_laser_red.png'))

# Player's Spaceship and bullet
yellowSpaceship = pygame.image.load(os.path.join('assets', 'pixel_ship_yellow.png'))
yellowLaserBullet = pygame.image.load(os.path.join('assets', 'pixel_laser_yellow.png'))

# Backgroud 
background = pygame.transform.scale(pygame.image.load(os.path.join('assets', 'background.png')), (width, height))

# Sound
laserSound = mixer.Sound(os.path.join('assets', 'laser.wav'))
collideSound = mixer.Sound(os.path.join('assets', 'explosion.wav'))


# Bullet class
class Laser:
	def __init__(self, x, y, img):
		self.x = x
		self.y = y
		self.img = img
		self.mask = pygame.mask.from_surface(self.img)

	def draw(self, window):
		window.blit(self.img, (self.x, self.y))

	def off_screen(self, height):
		return self.y >= height and self.y <= 0

	def move(self, vel):
		self.y += vel

	def collision(self, obj):
		# collideSound.play()
		return collide(self, obj)

# Abstract ship class
class Ship:
	COOLDOWN = 30
	def __init__(self, x, y, health = 100):
		self.x = x
		self.y = y
		self.health = health
		self.shipImage = None
		self.laserImage = None
		self.lasers = []
		self.coolDownCounter = 0

	def draw(self, window):
		window.blit(self.shipImage, (self.x, self.y))
		for laser in self.lasers:
			laser.draw(window)

	def get_width(self):
		return self.shipImage.get_width()

	def get_height(self):
		return self.shipImage.get_height()

	# Called by the enemies
	def move_lasers(self, vel, obj):
		self.cooldown()
		for laser in self.lasers:
			laser.move(vel)
			if laser.off_screen(height):
				self.lasers.remove(laser)
			elif laser.collision(obj):
				obj.health -= 10
				self.lasers.remove(laser)

	# Check if laser can be fired
	def cooldown(self):
		if self.coolDownCounter >= self.COOLDOWN:
			self.coolDownCounter = 0
		elif self.coolDownCounter > 0:
			self.coolDownCounter += 1

	# Creates the laser
	def shoot(self):
		if self.coolDownCounter == 0:
			laser = Laser(self.x, self.y, self.laserImage)
			self.lasers.append(laser)
			self.coolDownCounter = 1


# Player ship class
class Player(Ship):
	def __init__(self, x, y, health = 100):
		super().__init__(x, y, health)
		self.shipImage = yellowSpaceship
		self.laserImage = yellowLaserBullet
		self.maxHealth = health
		self.mask = pygame.mask.from_surface(self.shipImage)

	# Called by the player, duh!
	def move_lasers(self, vel, objs):
		self.cooldown()
		for laser in self.lasers:
			laser.move(vel)
			if laser.off_screen(height):
				self.lasers.remove(laser)
			else:
				for obj in objs:
					if laser.collision(obj):
						collideSound.play()
						objs.remove(obj)
						if laser in self.lasers:
							self.lasers.remove(laser)

	def draw(self, window):
		super().draw(window)
		self.healthbar(window)

	def healthbar(self, window):
		pygame.draw.rect(window, (255, 0, 0), (self.x, self.y + self.shipImage.get_height() + 10, self.shipImage.get_width(), 10))
		pygame.draw.rect(window, (0, 255, 0), (self.x, self.y + self.shipImage.get_height() + 10, self.shipImage.get_width() * (self.health/self.maxHealth), 10))


# Enemy ship class
class Enemy(Ship):
	COLORMAP = {
		"red" : (redSpaceship, redLaserBullet),
		"blue" : (blueSpaceship, blueLaserBullet),
		"green" : (greenSpaceship, greenLaserBullet)
	}

	def __init__(self, x, y, color, health = 100):
		super().__init__(x, y, health)
		self.shipImage, self.laserImage = self.COLORMAP[color]
		self.mask = pygame.mask.from_surface(self.shipImage)

	def move(self, vel):
		self.y += vel

	# Creates the laser
	def shoot(self):
		if self.coolDownCounter == 0:
			# Hardcoded solution. Fix dynamically
			laser = Laser(self.x - 10, self.y, self.laserImage) # Fix to shoot bullet from the center of the enemy ship
			self.lasers.append(laser)
			self.coolDownCounter = 1

# Function to check collision
def collide(object1, object2):
	offsetX = object2.x - object1.x
	offsetY = object2.y - object1.y
	return object1.mask.overlap(object2.mask, (offsetX, offsetY)) != None


def main():
	run = True
	FPS = 60
	clock = pygame.time.Clock()
	lives = 5
	level = 0

	playerVelocity = 5
	laserVelocity = 5

	lost  = False
	lostCount = 0

	enemies = []
	wave_length = 5
	enemyVelocity = 1

	mainFonts = pygame.font.SysFont('comicsans', 50)
	lostFonts = pygame.font.SysFont('comicsans', 70)

	player = Player(300, 620)

	# Function to draw characters/labels on screen
	def redraw_surface():
		displaySurface.blit(background, (0, 0))

		# Labels: lives, level, lost
		livesLabel = mainFonts.render(f"Lives: {lives}", 1, (255, 255, 255))
		levelLabel = mainFonts.render(f"Level: {level}", 1, (255, 255, 255))
		lostLabel = lostFonts.render("You Lost!!", 1, (255, 255, 255))
		# levelUpLabel = mainFonts.render("LEVEL UP!!", 1, (255, 255, 255))

		# Draw lives and level
		displaySurface.blit(livesLabel, (10, 10))
		displaySurface.blit(levelLabel, (width - levelLabel.get_width() - 10, 10))

		# Draw enemies
		for enemy in enemies:
			enemy.draw(displaySurface)

		if lost:
			displaySurface.blit(lostLabel, ((width / 2) - (lostLabel.get_width() / 2), 350))

		# Draw player
		player.draw(displaySurface)

		pygame.display.update()

	# Game Loop (Main loop)
	while run:
		clock.tick(FPS)
		redraw_surface()

		if lives <= 0 or player.health <=0:
			lost = True
			lostCount += 1

		if lost:
			if lostCount > FPS * 3:
				run = False
			else:
				continue


		# Creating enemies according to level
		if len(enemies) == 0:
			level += 1
			wave_length += 5
			for i in range(wave_length):
				enemy = Enemy(random.randrange(50, width - 100), random.randrange(-1500, -100), random.choice(["red", "blue", "green"]))
				enemies.append(enemy)

		# Checking for QUIT event
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()

		# Register keys
		keys = pygame.key.get_pressed()
		if keys[pygame.K_LEFT] and player.x - playerVelocity > 0: # moving to left
			player.x -= playerVelocity
		if keys[pygame.K_RIGHT] and player.x + playerVelocity + player.get_width() < width: # moving to right
			player.x += playerVelocity
		if keys[pygame.K_UP] and player.y - playerVelocity > 0: # moving up
			player.y -= playerVelocity
		if keys[pygame.K_DOWN] and player.y + playerVelocity + player.get_height() + 15 < height: # moving down
			player.y += playerVelocity
		if keys[pygame.K_SPACE]:
			laserSound.play()
			player.shoot()

		# Movement of enemies and lives counter
		for enemy in enemies[:]:
			enemy.move(enemyVelocity)
			enemy.move_lasers(laserVelocity, player)

			# Reason out the math behind the probability for range(0, 120) 
			# Probability: shoot 1s every 2 seconds
			if random.randrange(0, 2 * 60) == 1:
				enemy.shoot()

			if collide(enemy, player):
				player.health -= 10
				enemies.remove(enemy)
			elif enemy.y + enemy.get_height() > height:
				lives -= 1
				enemies.remove(enemy)


		
		player.move_lasers(-laserVelocity, enemies)

def main_menu():
	titleFont = pygame.font.SysFont('comicsans', 80)
	run = True
	while run:
		displaySurface.blit(background, (0, 0))
		titleLabel = titleFont.render("Press the mouse to play...", 1, (255, 255, 255))
		displaySurface.blit(titleLabel, (width / 2 - titleLabel.get_width() / 2, 350))

		pygame.display.update()
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				run = False
			if event.type == pygame.MOUSEBUTTONDOWN:
				main()
	pygame.quit()

if __name__ == '__main__':
	main_menu()








