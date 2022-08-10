import math
from typing import Tuple

import pygame


class RotatingRect:

    def __init__(self, x: int, y: int, width: int, height: int, alfa: float) -> None:
        self.x = x
        self.y = y
        self.w = width
        self.h = height
        self.alfa = alfa

        self.points = [(x - width // 2, y - height // 2),
                       (x + width // 2, y - height // 2),
                       (x + width // 2, y + height // 2),
                       (x - width // 2, y + height // 2)]
        self.rot_points = []
        self.rotate()

    def rotate(self):
        ang = math.radians(self.alfa)

        matrix = [[math.cos(ang), math.sin(ang)], [-math.sin(ang), math.cos(ang)]]

        for vertex in self.points:
            matrix2 = [[vertex[0] - self.x], [vertex[1] - self.y]]
            matrix3 = [[self.x], [self.y]]

            rot_vertex = add_mat(mul_mats(matrix, matrix2), matrix3)
            self.rot_points.append((rot_vertex[0][0], rot_vertex[1][0]))

    def collidepoint(self, point: Tuple[int, int]) -> bool:
        n = 0
        for i in range(4):
            a, b = self.rot_points[i], self.rot_points[i - 1]

            (x, y), t, k = line_to_line_intersection3(point, (point[0] + 1200, point[1] + 1200), a, b)
            if 0 < -k < 1 and x >= point[0] and y >= point[1]:
                n += 1
        return n % 2 == 1

    def render(self, surf: pygame.Surface, color: Tuple[int, int, int]) -> None:
        pygame.draw.circle(surf, color, (self.x, self.y), 4)
        for i in range(len(self.rot_points)):
            pygame.draw.line(surf, color, self.rot_points[i-1], self.rot_points[i])


def mul_mats(mat1, mat2):  # Function for multiplying 2 matrices
    if len(mat1[0]) != len(mat2):
        raise ValueError("Matrix 1 must have same number of rows as matrix 2 has columns!")

    res = [[0 for _ in range(len(mat2[0]))] for _ in range(len(mat1))]

    for i in range(len(mat1)):
        for j in range(len(mat2[0])):
            for k in range(len(mat2)):
                res[i][j] += mat1[i][k] * mat2[k][j]

    return res


def add_mat(mat1, mat2):  # Function for adding up 2 matrices
    if len(mat1) != len(mat2) or len(mat1[0]) != len(mat2[0]):
        raise ValueError("Matrices must have same topology!")

    res = mat1.copy()

    for i in range(len(mat1)):
        for j in range(len(mat1[0])):
            res[i][j] = mat1[i][j] + mat2[i][j]

    return res


def line_to_line_intersection3(point1, q1, point2, q2):
    Vx = point1[0] - q1[0]
    Vy = point1[1] - q1[1]
    Vz = point2[0] - q2[0]
    Vw = point2[1] - q2[1]

    x0 = point1[0]
    y0 = point1[1]
    z0 = point2[0]
    w0 = point2[1]

    D = det([[[Vx], [-Vz]], [[Vy], [-Vw]]])
    Dt = det([[[z0 - x0], [-Vz]], [[w0 - y0], [-Vw]]])
    Dk = det([[[Vx], [z0 - x0]], [[Vy], [w0 - y0]]])
    if D == 0:
        return None, None, None

    t = Dt / D
    k = Dk / D

    intersection = x0 + Vx * t, y0 + Vy * t

    return intersection, t, k


def det(mat, mul=1):  # Returns the determinant of a matrix
    matrix = mat.copy()
    width = len(matrix)
    if width == 1:
        return mul * matrix[0][0][0]
    sign = -1
    answer = 0
    for i in range(width):
        m = []
        for j in range(1, width):
            buff = [matrix[j][k] for k in range(width) if k != i]
            m.append(buff)
        sign *= -1
        answer += mul * det(m, sign * matrix[0][i][0])
    return answer

