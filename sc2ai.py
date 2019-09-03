import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import GATEWAY, NEXUS, PROBE, PYLON, ASSIMILATOR, CYBERNETICSCORE, STALKER, STARGATE, VOIDRAY
import random
import cv2
	

class SentdeBot(sc2.BotAI):
	async def on_step(self, iteration):
		await self.distribute_workers()
		await self.build_pylons()
		await self.build_workers()
		await self.expand()
		await self.build_assimilator()
		await self.offensive_force_buildings()
		await self.build_offensive_force()
		await self.attack()
		self.iteration = iteration

	def __init__(self):
		self.ITERATIONS_PER_MINUTE = 165
		self.MAX_WORKERS = 50
		self.iteration = 0

	def find_target(self,state):
		if len(self.known_enemy_units) > 0:
			return random.choice(self.known_enemy_units)
		elif len(self.known_enemy_structures) > 0:
			return random.choice(self.known_enemy_units)
		else:
			return self.enemy_start_locations[0]


	async def attack(self):

		aggressive_units = {STALKER: [15,5], VOIDRAY:[8,3]}

		for UNIT in aggressive_units:
			if self.units(UNIT).amount > aggressive_units[UNIT][0] and self.units(UNIT).amount > aggressive_units[UNIT][1]:
				for s in self.units(UNIT).idle:
					await self.do(s.attack(self.find_target(self.state)))

			elif self.units(UNIT).amount > aggressive_units[UNIT][1]:
					if len(self.known_enemy_units) > 0:
						for s in self.units(UNIT).idle:
							await self.do(s.attack(random.choice(self.known_enemy_units)))

		if self.units(STALKER).amount > 3:
			if len(self.known_enemy_units) > 0:
				for s in self.units(STALKER).idle:
					await self.do(s.attack(random.choice(self.known_enemy_units)))
		elif self.units(STALKER).amount > 15:
			for s in self.units(STALKER).idle:
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



	async def build_assimilator(self):
		for nexus in self.units(NEXUS).ready:
			vaspenes = self.state.vespene_geyser.closer_than(25.0, nexus)
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

