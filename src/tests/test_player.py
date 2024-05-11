from src.Player import *
from src.Region import Region

from unittest import TestCase

class PlayerTests(TestCase):
    def test_player(self):
        player = Player(1, Region(Region.NA), 100, 0, 0, 1500, 0, 0, 0, 1500, None, Race.TERRAN)
        self.assertEqual(player.id, 1)
        self.assertEqual(player.region.region, Region.NA)
        self.assertEqual(player.zwins, 100)
        self.assertEqual(player.zloses, 0)
        self.assertEqual(player.zties, 0)
        self.assertEqual(player.zelo, 1500)
        self.assertEqual(player.twins, 0)
        self.assertEqual(player.tloses, 0)
        self.assertEqual(player.tties, 0)
        self.assertEqual(player.telo, 1500)
        self.assertIsNone(player.lastPlayed)
        self.assertEqual(player.racePref.race, Race.TERRAN)

    def test_valid_region(self):
        self.assertTrue(Region.Valid(Region(Region.EU)))
        self.assertTrue(Region.Valid(Region(Region.NA)))
        self.assertTrue(Region.Valid(Region(Region.ALL)))

    def test_invalid_region(self):
        self.assertFalse(Region.Valid(Region('blah')))