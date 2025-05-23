import Meteomatrice
from matrice import *
from Horlogematrice import *
from Meteomatrice import *

class Display:
    def __init__(self):
        self.matrice = Matrice(10, 256)

    def draw_shape(self, shape_matrix, start_row, start_col, color=None, color_matrix=None):
        """
        Dessine une forme sur la matrice LED.

        :param shape_matrix: Matrice définissant la forme à dessiner (1 pour allumé, 0 pour éteint).
        :param start_row: Ligne de départ pour dessiner la forme.
        :param start_col: Colonne de départ pour dessiner la forme.
        :param color: Couleur unique pour toute la forme (optionnel si color_matrix est fourni).
        :param color_matrix: Matrice des couleurs pour chaque pixel de la forme (optionnel si color est fourni).
        """
        self.matrice.draw(shape_matrix, start_row, start_col, color, color_matrix)

    def draw_sun(self):
        self.draw_shape(SUN, 1, 1, color=(100, 100, 0))

    def draw_rain(self):
        self.draw_shape(RAIN, 1, 1, color_matrix=RAIN_COLOR)

    def draw_cloud(self):
        self.draw_shape(CLOUD, 1, 1, color=(100, 100, 100))

    def draw_dark_cloud(self):
        self.draw_shape(CLOUD, 1, 1, color=(10, 10, 10))

    def draw_cloud_and_sun(self):
        self.draw_shape(CLOUDNSUN, 1, 1, color_matrix=CLOUDNSUN_COLOR)






