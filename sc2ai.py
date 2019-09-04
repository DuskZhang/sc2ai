import sc2
from sc2 import run_game, maps, Race, Difficulty, position
from sc2.player import Bot, Computer
from sc2.constants import GATEWAY, NEXUS, PROBE, PYLON, ASSIMILATOR, CYBERNETICSCORE, STALKER, STARGATE, VOIDRAY, ROBOTICSFACILITY, OBSERVER
import random
import cv2
import numpy as np
	

class SentdeBot(sc2.BotAI):
	async def on_step(self, iteration):
		self.iteration = iteration
		await self.distribute_workers()
		await self.build_pylons()
		await self.build_workers()
		await self.expand()
		await self.build_assimilator()
		await self.offensive_force_buildings()
		await self.build_offensive_force()
		await self.attack()
		await self.intel()
		await self.scout()
		

	def __init__(self):
		self.ITERATIONS_PER_MINUTE = 165
		self.MAX_WORKERS = 50
		self.iteration = 0

	def random_location_variance(self,enemy_start_location):
		x = enemy_start_location[0]
		y = enemy_start_location[1]

		x += ((random.randrange(-20,20))/100) * enemy_start_location[0]
		y += ((random.randrange(-20,20))/100) * enemy_start_location[1]

		if x < 0:
			x = 0
		if y < 0:
			y = 0
		if x > self.game_info.map_size[0]:
			x = self.game_info.map_size[0]
		if y > self.game_info.map_size[1]:
			y = self.game_info.map_size[1]

		go_to = position.Point2(position.Pointlike((x,y)))
		return go_to

	async def scout(self):
		line_max = 50
		mineral_ratio = self.minerals/1500
		if mineral_ratio > 1.0:
			mineral_ratio = 1.0

		vespene_ratio = self.vespene / 1500
		if vespene_ratio > 1.0:
			vespene_ratio = 1.0

		population_ratio = self.supply_left / self.supply_cap
		if population_ratio > 1.0:
			population_ratio = 1.0

		plausible_ supply = self.supply_cap/200.0

		military_weight = len(self.units(VOIDRAY)) / (self.supply_cap - self.supply_left)
		if military_weight > 1.0:
			military_weight = 1.0


		cv2.line(game_data , (0,19), (int(line_max * military_weight),19), (250, 250,200), 3)	
		v2.line(game_data , (0,15), (int(line_max * plausible_supply),15), (220, 200,200), 3)
		v2.line(game_data , (0,11), (int(line_max * population_ratio),11), (150, 150,150), 3)
		v2.line(game_data , (0,7), (int(line_max * vespene_ratio),7), (210, 200,0), 3)
		v2.line(game_data , (0,3), (int(line_max * mineral_ratio),3), (0, 255,25), 3)
		if len(self.units(OBSERVER)) > 0:
			scout = self.units(OBSERVER)[0]
			if scout.is_idle:
				enemy_location = self.enemy_start_locations[0]
				move_to = self.random_location_variance(enemy_location)
				print(move_to)
				await self.do(scout.move(move_to))

		else: 
			for rf in self.units(ROBOTICSFACILITY).ready.noqueue:
				if self.can_afford(OBSERVER) and self.supply_left > 0:
					await self.do(rf.train(OBSERVER))
	
	async def intel(self):
		print(self.game_info.map_size)
		game_data = np.zeros((self.game_info.map_size[1], self.game_info.map_size[0], 3), np.uint8)
		for nexus in self.units(NEXUS):
			nex_pos = nexus.position
			print(nex_pos)
			cv2.circle(game_data, (int(nex_pos[0]), int(nex_pos[1])), 10, (0,255,0), -1)
		flipped = cv2.flip(game_data,0)
		resized = cv2.resize(flipped, dsize = None, fx=2,fy = 2)

		cv2.imshow('Intel', resized)
		cv2.waitKey(1)
		draw_dict = {
			NEXUS: [15, (0,255,0)],
			PYLON: [3, (20,235,0)],
			PROBE:[1,(55, 200, 0)],
			ASSIMILATOR: [2, (55,200,0)],
			GATEWAY: [3,(200,100,0)],
			CYBERNETICSCORE: [3,(200,100,0)],
			STARGATE: [5,(255,0,0)],
			VOIDRAY:[3,(255,100,0)],
			ROBOTICSFACILITY:[5,(215,155,0)],
			#OBSERVER: [3,(255,255,255)],

		}
		for obs in self.units(OBSERVER).ready:
			pos = obs.position
			cv2.circle(game_data, (int(pos[0]), int(pos[1])), 1 ,(255,255,255), -1) 

		for unit_type in draw_dict:
			for unit in self.units(unit_type).ready:
				pos = unit.position
				cv2.circle(game_data,(int(pos[0]), int(pos[1])),draw_dict[unit_type][0], draw_dict[unit_type][1], -1)
	
		main_base_names = ["nexus", "commandcenter", "hatchery"]
		for enemy_building in self.known_enemy_structures:
			pos = enemy_building.position
			if enemy_building.name.lower() not in main_base_names:
				cv2.circle(game_data, (int(pos[0]), int(pos[1])), 5, (200, 50, 212), -1)

		for enemy_building in self.known_enemy_structures:
			pos = enemy_building.position
			if enemy_building.name.lower() in main_base_names:
				cv.circle(game_data, (int(pos[0]), int(pos[1])), 15, (0,0,255), -1)

		for enemy_unit in self.known_enemy_units:

			if not enemy_unit.is_structure:
				worker_names = ["probe",
								"scv",
								"drone"]

				pos = enemy_unit.position
				if enemy_unit.name.lower() in worker_names:
					cv2.circle(game_data,(int(pos[0]), int(pos[1])), 1, (55,0,155), -1)
				else:
					cv2.circle(game_data, (int(pos[0]), int(pos[1])), 1, (21,21,21), -1)

	def find_target(self,state):
		if len(self.known_enemy_units) > 0:
			return random.choice(self.known_enemy_units)
		elif len(self.known_enemy_structures) > 0:
			return random.choice(self.known_enemy_units)
		else:
			return self.enemy_start_locations[0]


	async def attack(self):

		aggressive_units = {VOIDRAY:[8,3]}

		for UNIT in aggressive_units:
			for s in self.units(UNIT).idle:
					await self.do(s.attack(self.find_target(self.state)))

	async def build_offensive_force(self):
		for sg in self.units(STARGATE).ready.noqueue:
			if self.can_afford(VOIDRAY) and self.supply_left > 0:
				await self.do(sg.train(VOIDRAY))


	async def offensive_force_buildings(self):
		if self.units(PYLON).ready.exists:
			pylon = self.units(PYLON).ready.random

			if self.units(GATEWAY).ready.exists and not self.units(CYBERNETICSCORE):
				if self.can_afford(CYBERNETICSCORE) and not self.already_pending(CYBERNETICSCORE):
					await self.build(CYBERNETICSCORE, near=pylon)
			
			elif len(self.units(GATEWAY)) == 0:
				if self.can_afford(GATEWAY) and not self.already_pending(GATEWAY):
					await self.build(GATEWAY, near=pylon)

			if self.units(CYBERNETICSCORE).ready.exists:
				if len(self.units(STARGATE)) < self.iteration / self.ITERATIONS_PER_MINUTE:
					if self.can_afford(STARGATE) and not self.already_pending(STARGATE):
						await self.build(STARGATE, near = pylon)

			if self.units(CYBERNETICSCORE).ready.exists:
				if len(self.units(ROBOTICSFACILITY)) < 1:
					if self.can_afford(ROBOTICSFACILITY) and not self.already_pending(ROBOTICSFACILITY):
						await self.build(ROBOTICSFACILITY,near = pylon)



	async def build_assimilator(self):
		for nexus in self.units(NEXUS).ready:
			vaspenes = self.state.vespene_geyser.closer_than(15.0, nexus)
			for vaspene in vaspenes:
				if not self.can_afford(ASSIMILATOR):
					break
			worker = self.select_build_worker(vaspene.position)
			if worker is None:
				break
			if not self.units(ASSIMILATOR).closer_than(1.0, vaspene).exists:
				await self.do(worker.build(ASSIMILATOR, vaspene))
	

	async def build_workers(self):
		if(len(self.units(NEXUS)) * 16) > len(self.units(PROBE)) and self.MAX_WORKERS > len(self.units(PROBE)):
			for nexus in self.units(NEXUS).ready.noqueue:
				if self.can_afford(PROBE):
					await self.do(nexus.train(PROBE))


	async def build_pylons(self):
		if self.supply_left < 5 and not self.already_pending(PYLON):
			nexuses = self.units(NEXUS).ready
			if nexuses.exists:
				if self.can_afford(PYLON):
					await self.build(PYLON, near= nexuses.first)


	async def expand(self):
		if self.units(NEXUS).amount < (self.iteration/ self.ITERATIONS_PER_MINUTE / 2) and self.can_afford(NEXUS):
			await self.expand_now()


run_game(maps.get("AbyssalReefLE"), [ 
	Bot(Race.Protoss, SentdeBot()),
	Computer(Race.Terran, Difficulty.Easy)
	], realtime = True)

