import datetime
import os
import sys
import uuid
from collections import Counter
from random import randint

import config as cfg
from cursesmenu import CursesMenu
from cursesmenu.items import FunctionItem, SubmenuItem
from database import Database
from functions import cls
from interface import Interface
from rich.prompt import Prompt


class Dice():
    __value = 0
    __nb_face = 6

    def _roll(self):
        self.__value = randint(1, self.__nb_face)

    def _getValue(self):
        return self.__value


class Score():
    __database = Database.get_instance()

    def __init__(self, gameId) -> None:
        self.__gameId = gameId

    def addScore(self, name, score):
        self.__database.updateScore(self.__gameId, name, score)

    def getScores(self):
        return self.__database.getDBScore(self.__gameId)

    def findScore(self, name):
        return self.__database.getDBScore(self.__gameId)[name]

    def getRemainCombination(self):
        return Counter(
            self.__database.getDBScore(self.__gameId).values()
        ).get(None)

    def getTotalScore(self):
        return sum(
            [i for i in self.__database.getDBScore(
                self.__gameId
            ).values() if i is not None]
        )


class Combination(Score):

    __available_combinations = {}
    sacrified = True

    def __init__(self, score) -> None:
        self.__score = score

    def __addCombination(self, name, value):
        if self.__score.findScore(name) is None:
            self.__available_combinations[name] = value

    def clearAvailableCombinations(self):
        self.__available_combinations.clear()

    def isNumber(self, dices):
        for k, v in Counter(dices).items():
            self.__addCombination(str(k), k*v)

    def isBrelan(self, dices):
        for k, v in Counter(dices).items():
            if v == 3:
                self.__addCombination('brelan', k*v)

    def isFull(self, dices):
        if 3 in Counter(dices).values() and 2 in Counter(dices).values():
            self.__addCombination('full', 25)

    def isCarre(self, dices):
        for k, v in Counter(dices).items():
            if v == 4:
                self.__addCombination('carre', k*v)

    def isYams(self, dices):
        for k, v in Counter(dices).items():
            if v == 5:
                self.__addCombination('yams', k*v)

    def isSequence(self, dices):
        suite = []
        for idx, item in enumerate(sorted(Counter(dices))):
            if not idx or item - 1 != suite[-1][-1]:
                if len(suite) < 1:
                    suite.append([item])
            else:
                suite[-1].append(item)
        if len(suite[0]) == 4:
            self.__addCombination('smallSequence', 30)
        if len(suite[0]) == 5:
            self.__addCombination('largeSequence', 40)

    def isChance(self, dices):
        self.__addCombination('chance', sum(dices))

    # Get combination of the last roll
    def getCombination(self, values):
        self.clearAvailableCombinations()

        values.sort()
        self.isNumber(values)
        self.isBrelan(values)
        self.isCarre(values)
        self.isYams(values)
        self.isFull(values)
        self.isChance(values)
        self.isSequence(values)

        # Return list of combination
        return self.__available_combinations

    def searchCombinationKey(self, key):
        for k, v in cfg.combinationsList.items():
            if v == key:
                return k


class NewGame():
    __interface = Interface()
    __database = Database.get_instance()
    nb_dices = 5
    __dices = []
    __reroll_remain = 2
    __already_rolled = []

    # Init dices and create instance of them
    def __init__(self):
        self.__dices = []
        for _ in range(self.nb_dices):
            self.__dices.append(Dice())

        self.rerollAll()
        self.play()

    def rerollAll(self):
        for x in range(len(self.__dices)):
            self.__dices[x]._roll()

    def getDatabaseScores(self):
        return self.__database.getAllScores()

    def clearRound(self):
        self.__reroll_remain = 2
        self.__combination.clearAvailableCombinations()
        self.__combination.sacrified = True

    # Get values of all dices
    def getValues(self):
        dices_values = []
        for x in self.__dices:
            dices_values.append(x._getValue())
        return dices_values

    def reroll(self):
        while self.__reroll_remain > 0:
            while True:
                try:
                    self.__already_rolled.clear()
                    self.__interface.clearErrorPanel()
                    self.__interface.generateCombinationsTableData(
                        self.__combination.getCombination(
                            self.getValues()
                        ).items()
                    )
                    self.__interface.addDialogText(
                        'How many dice do you want to roll again? [0 - ' + str(
                            self.nb_dices) + ']'
                    )

                    self.reroll_count = int(Prompt.ask("\n"))
                    if self.reroll_count > 0 and self.reroll_count <= 5:
                        self.__reroll_remain -= 1
                        break
                    elif self.reroll_count == 0:
                        self.__reroll_remain = 0
                        break
                    elif self.reroll_count > 5:
                        self.__interface.generateErrorPanel(
                            'No more than 5 dice can be re-rolled.')
                    else:
                        self.__interface.generateErrorPanel('Error !')
                except ValueError:
                    self.__interface.generateErrorPanel(
                        'Please enter a valid number.')

            for _ in range(self.reroll_count):
                while True:
                    try:
                        self.__interface.addDialogText(
                            'Which dice do you want to roll again?', True)
                        rerollDice = int(Prompt.ask("\nDice Number"))
                        if rerollDice in self.__already_rolled:
                            self.__interface.generateErrorPanel(
                                'You cannot reroll this dice more than once!')
                        elif type(rerollDice) is int and (
                            rerollDice <= 5
                        ) and (rerollDice) > 0:
                            self.__already_rolled.append(rerollDice)
                            break
                        else:
                            self.__interface.generateErrorPanel(
                                'You cannot reroll this dice ' +
                                'because it does not exist!'
                            )
                    except ValueError:
                        self.__interface.generateErrorPanel(
                            'Please enter a valid number.')

                self.__dices[rerollDice - 1]._roll()
                self.__interface.generateDicesTableData(self.__dices)

            self.__interface.generateCombinationsTableData(
                self.__combination.getCombination(self.getValues()).items())

    def play(self):
        self.__gameId = str(uuid.uuid4()).replace('-', '')
        self.__database.setGameId(self.__gameId)
        self.__score = Score(self.__gameId)
        self.__combination = Combination(self.__score)

        for _ in range(self.__score.getRemainCombination()):
            # Roll all dices and save all values in array
            self.__interface.generateScoreTableData(
                self.__score.getScores().items())
            self.__interface.generateDicesTableData(self.__dices)
            self.reroll()

            if len(self.__combination.getCombination(
                self.getValues()).items()
            ) == 0:
                self.__interface.generateErrorPanel(
                    'No combination is available for this roll.')
                notCompletedScores = [
                    (k, v) for k, v in self.__score.getScores().items()
                    if v is None]
                self.__interface.generateCombinationsTableData(
                    notCompletedScores)
                self.__interface.addDialogText(
                    'Which combination do you want to sacrifice? [0 - ' + str(
                        len(notCompletedScores)
                    ) + ']', True)
                rerollDice = int(Prompt.ask("\nCombination number"))

                self.__score.addScore(notCompletedScores[rerollDice][0], 0)
                self.__combination.sacrified = False

                # self.__combination.sacrificeCombination()

            while self.__combination.sacrified:
                try:
                    self.__interface.generateScoreTableData(
                        self.__score.getScores().items())
                    self.__interface.addDialogText(
                        'Which one do you choose?', True)
                    combinationChoose = int(Prompt.ask('\n'))
                    if combinationChoose >= 0 and combinationChoose < len(
                        self.__combination.getCombination(
                            self.getValues()
                        ).items()
                    ):
                        combinationChosed = list(
                            self.__combination.getCombination(
                                self.getValues()).items())[combinationChoose]
                        break
                    elif combinationChoose > len(
                        self.__combination.getCombination(
                            self.getValues()
                        ).items()
                    ):
                        self.__interface.generateErrorPanel(
                            "Please choose a valid number from the list!")
                    else:
                        self.__interface.generateErrorPanel('Error !')
                except ValueError:
                    self.__interface.generateErrorPanel(
                        'Please enter a valid number.')
            self.__score.addScore(
                combinationChosed[0], int(combinationChosed[1]))
            self.__interface.addDialogText("New round ! " + str(
                self.__score.getRemainCombination()) +
                " rounds before the end of the game !", True)
            self.rerollAll()
            self.clearRound()


class LoadGame():
    __interface = Interface()
    __database = Database.get_instance()
    nb_dices = 5
    __dices = []
    __reroll_remain = 2
    __already_rolled = []

    # Init dices and create instance of them
    def __init__(self, gameId):
        self.__dices = []
        for _ in range(self.nb_dices):
            self.__dices.append(Dice())

        self.__score = Score(gameId)
        self.__combination = Combination(self.__score)

        self.rerollAll()
        self.play()

    def rerollAll(self):
        for x in range(len(self.__dices)):
            self.__dices[x]._roll()

    def getDatabaseScores(self):
        return self.__database.getAllScores()

    def clearRound(self):
        self.__reroll_remain = 2
        self.__combination.clearAvailableCombinations()
        self.__combination.sacrified = True

    # Get values of all dices
    def getValues(self):
        dices_values = []
        for x in self.__dices:
            dices_values.append(x._getValue())
        return dices_values

    def reroll(self):
        while self.__reroll_remain > 0:
            while True:
                try:
                    self.__already_rolled.clear()
                    self.__interface.clearErrorPanel()
                    self.__interface.generateCombinationsTableData(
                        self.__combination.getCombination(
                            self.getValues()
                        ).items()
                    )
                    self.__interface.addDialogText(
                        'How many dice do you want to roll again? [0 - ' + str(
                            self.nb_dices) + ']'
                    )

                    self.reroll_count = int(Prompt.ask("\n"))
                    if self.reroll_count > 0 and self.reroll_count <= 5:
                        self.__reroll_remain -= 1
                        break
                    elif self.reroll_count == 0:
                        self.__reroll_remain = 0
                        break
                    elif self.reroll_count > 5:
                        self.__interface.generateErrorPanel(
                            'No more than 5 dice can be re-rolled.')
                    else:
                        self.__interface.generateErrorPanel('Error !')
                except ValueError:
                    self.__interface.generateErrorPanel(
                        'Please enter a valid number.')

            for _ in range(self.reroll_count):
                while True:
                    try:
                        self.__interface.addDialogText(
                            'Which dice do you want to roll again?', True)
                        rerollDice = int(Prompt.ask("\nDice Number"))
                        if rerollDice in self.__already_rolled:
                            self.__interface.generateErrorPanel(
                                'You cannot reroll this dice more than once!')
                        elif type(rerollDice) is int and (
                            rerollDice <= 5
                        ) and (rerollDice) > 0:
                            self.__already_rolled.append(rerollDice)
                            break
                        else:
                            self.__interface.generateErrorPanel(
                                'You cannot reroll this dice ' +
                                'because it does not exist!'
                            )
                    except ValueError:
                        self.__interface.generateErrorPanel(
                            'Please enter a valid number.')

                self.__dices[rerollDice - 1]._roll()
                self.__interface.generateDicesTableData(self.__dices)

            self.__interface.generateCombinationsTableData(
                self.__combination.getCombination(self.getValues()).items())

    def play(self):
        for _ in range(self.__score.getRemainCombination()):
            # Roll all dices and save all values in array
            self.__interface.generateScoreTableData(
                self.__score.getScores().items())
            self.__interface.generateDicesTableData(self.__dices)
            self.reroll()

            if len(self.__combination.getCombination(
                self.getValues()).items()
            ) == 0:
                self.__interface.generateErrorPanel(
                    'No combination is available for this roll.')
                notCompletedScores = [
                    (k, v) for k, v in self.__score.getScores().items()
                    if v is None]
                self.__interface.generateCombinationsTableData(
                    notCompletedScores)
                self.__interface.addDialogText(
                    'Which combination do you want to sacrifice? [0 - ' + str(
                        len(notCompletedScores)
                    ) + ']', True)
                rerollDice = int(Prompt.ask("\nCombination number"))

                self.__score.addScore(notCompletedScores[rerollDice][0], 0)
                self.__combination.sacrified = False

                # self.__combination.sacrificeCombination()

            while self.__combination.sacrified:
                try:
                    self.__interface.generateScoreTableData(
                        self.__score.getScores().items())
                    self.__interface.addDialogText(
                        'Which one do you choose?', True)
                    combinationChoose = int(Prompt.ask('\n'))
                    if combinationChoose >= 0 and combinationChoose < len(
                        self.__combination.getCombination(
                            self.getValues()
                        ).items()
                    ):
                        combinationChosed = list(
                            self.__combination.getCombination(
                                self.getValues()).items())[combinationChoose]
                        break
                    elif combinationChoose > len(
                        self.__combination.getCombination(
                            self.getValues()
                        ).items()
                    ):
                        self.__interface.generateErrorPanel(
                            "Please choose a valid number from the list!")
                    else:
                        self.__interface.generateErrorPanel('Error !')
                except ValueError:
                    self.__interface.generateErrorPanel(
                        'Please enter a valid number.')
            self.__score.addScore(
                combinationChosed[0], int(combinationChosed[1]))
            self.__interface.addDialogText("New round ! " + str(
                self.__score.getRemainCombination()) +
                " rounds before the end of the game !", True)
            self.rerollAll()
            self.clearRound()


class Game():
    def __new__(self, *gameId):
        if len(gameId) == 0:
            return NewGame()
        else:
            return LoadGame(gameId[0])


class Menu():

    __menu = CursesMenu("Yam's Game", "Main Menu")
    __historyMenu = CursesMenu("Game History", "History Menu")
    __historyMenu.parent = __menu

    __database = Database.get_instance()

    def menu(self):
        cls()
        for game in self.__database.getAllScores():
            date = datetime.datetime.strptime(
                str(game['createdAt']),
                '%Y-%m-%d %H:%M:%S.%f').strftime("%d/%m/%Y %H:%M:%S")
            self.__historyMenu.items.append(FunctionItem(
                str(date) + " - Score: (%s)" % (game['scoreSum']),
                Game, (game['gameId'],)))

        self.__menu.items.append(FunctionItem("Start Game", Game))
        self.__menu.items.append(SubmenuItem(
            "History", self.__historyMenu, self.__menu, True))
        self.__menu.show()


try:
    game = Menu()
    game.menu()
except KeyboardInterrupt:
    try:
        sys.exit(0)
    except SystemExit:
        os._exit(0)
