import machine
import neopixel

class Matrice:
    def __init__(self, led_pin, num_leds):
        self.led_pin = led_pin
        self.num_leds = num_leds
        self.np = neopixel.NeoPixel(machine.Pin(self.led_pin), self.num_leds)

    def set_color(self, index, color):
        """Définit la couleur d'une LED spécifique."""
        if 0 <= index < self.num_leds:
            self.np[index] = color

    def clear_strip(self):
        """Éteint toutes les LEDs de la matrice."""
        for i in range(self.num_leds):
            self.np[i] = (0, 0, 0)
        self.np.write()

    def index_in_matrix(self, row, col):
        """Calcule l'index de la LED dans le tableau en fonction de sa position en ligne et colonne."""
        if col % 2 == 0:
            return col * self.height + row
        else:
            return col * self.height + (self.height - 1 - row)
        # if col % 2 == 0:
        #     return col * 8 + row
        # else:
        #     return col * 8 + (7 - row)

    def draw(self, shape_matrix, start_row, start_col, color=None, color_matrix=None):
        """
        Dessine une forme sur la matrice LED.

        :param shape_matrix: Matrice définissant la forme à dessiner (1 pour allumé, 0 pour éteint).
        :param start_row: Ligne de départ pour dessiner la forme.
        :param start_col: Colonne de départ pour dessiner la forme.
        :param color: Couleur unique pour toute la forme (optionnel si color_matrix est fourni).
        :param color_matrix: Matrice des couleurs pour chaque pixel de la forme (optionnel si color est fourni).
        """
        rows = len(shape_matrix)
        cols = len(shape_matrix[0])

        for r in range(rows):
            for c in range(cols):
                if shape_matrix[r][c] == 1:
                    index = self.index_in_matrix(start_row + r, start_col + c)
                    if color_matrix:
                        pixel_color = color_matrix[r][c]
                    else:
                        pixel_color = color
                    self.set_color(index, pixel_color)
        self.np.write()

    def wheel(self, pos):
        """
        Change la matrice en un arc-en-ciel fabuleux
        """
        if pos < 85:
            return (pos * 3, 255 - pos * 3, 0)
        elif pos < 170:
            pos -= 85
            return (255 - pos * 3, 0, pos * 3)
        else:
            pos -= 170
            return (0, pos * 3, 255 - pos * 3)

    def slide(self,matrix, start_row, wait, colorfull):
        """
        Fais defiler les matrices
        """
        rows = len(matrix)
        cols = len(matrix[0])

        for offset in range(-15, cols):
            self.clear_strip()
            for r in range(16):
                for c in range(16):
                    matrix_col = c + offset
                    if 0 <= matrix_col < cols and 0 <= start_row + r < rows:
                        if matrix[start_row + r][matrix_col] == 1:
                            if colorfull:
                                color = self.wheel((r * 16 + c) & 255)
                            else :
                                color = (10, 10, 10)
                            index = self.index_in_matrix(r, c)
                            self.set_color(index, color)
            self.np.write()
            time.sleep_ms(wait)
        self.clear_strip()
