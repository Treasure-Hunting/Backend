from django.db import models

from . import Difficulty, Quiz


class Player(models.Model):
    difficulty = models.ForeignKey(Difficulty, on_delete=models.CASCADE)
    quizzes = models.ManyToManyField(Quiz)
