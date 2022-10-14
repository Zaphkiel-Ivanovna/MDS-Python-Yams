import config as cfg
from rich import box
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table


class Interface():
    __console = Console()
    __layout = Layout(name="root")
    __dialogTexts = []

    def __init__(self) -> None:
        self.__dicesTable = self.__createDicesTable()
        self.__combinationsTable = self.__createCombinationsTable()
        self.__scoresTable = self.__createScoresTable()

        grid = Table.grid(expand=True)
        grid.add_column(justify="center", ratio=1)
        grid.add_column(justify="right")
        grid.add_row("Yam's Game", "by DUBERNET Damien")

        self.__layout.split(
            Layout(name="blank", size=3),
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="errors", size=6),
            Layout(name="body", size=6),
        )

        self.__layout["main"].split_row(
            Layout(self.__dicesTable, name="dicesTable"),
            Layout(self.__combinationsTable, name="combinationsTable"),
            Layout(self.__scoresTable, name="scoreTable"),
        )

        self.__layout["blank"].update("")
        self.__layout["combinationsTable"].update("")
        self.__layout["header"].update(Panel(grid, style="white on dark_red"))
        self.__layout["body"].update(Panel("", title="Dialog", style="white"))
        self.__layout["errors"].update(Panel("", title="Errors", style="red"))

    def __createDicesTable(self) -> Table:
        __dicesTable = Table(box=box.ROUNDED)
        __dicesTable.add_column("Dice", justify="right",
                                style="cyan", no_wrap=True)
        __dicesTable.add_column("Result", style="white", justify="center")
        return __dicesTable

    def __createScoresTable(self) -> Table:
        __scoresTable = Table(box=box.ROUNDED)
        __scoresTable.add_column(
            "Combination", justify="right", style="cyan", no_wrap=True)
        __scoresTable.add_column("Points", style="white", justify="center")
        return __scoresTable

    def __createCombinationsTable(self) -> Table:
        __combinationsTable = Table(box=box.ROUNDED)
        __combinationsTable.add_column("ID", style="white", justify="center")
        __combinationsTable.add_column(
            "Available Combination",
            justify="right",
            style="cyan",
            no_wrap=True)
        __combinationsTable.add_column(
            "Points earned", style="white", justify="center")
        return __combinationsTable

    def addDialogText(self, text, clear=False):
        if (clear is True):
            self.__dialogTexts.clear()

        self.__dialogTexts.append(text)
        self.__layout["body"].update(
            Panel(
                '\n\n'.join(self.__dialogTexts),
                title="Dialog",
                style="white"
            ))
        self.showInterface()

    def generateErrorPanel(self, text):
        self.clearErrorPanel()
        self.__layout["errors"].update(
            Panel("[red]" + text, title="Errors", style="red"))
        self.showInterface()

    def generateDicesTableData(self, dices):
        self.__dicesTable = self.__createDicesTable()
        for x in range(5):
            if x == 4:
                self.__dicesTable.add_row(
                    "Dice n°" + str(x + 1), str(dices[x]._getValue()))
            else:
                self.__dicesTable.add_row(
                    "Dice n°" + str(x + 1), str(dices[x]._getValue()) + "\n")
        self.__layout["dicesTable"].update(self.__dicesTable)

    def generateScoreTableData(self, scores):
        self.__scoresTable = self.__createScoresTable()
        for k, v in scores:
            if v is None:
                v = ''
            self.__scoresTable.add_row(
                str(cfg.combinationsList.get(k)), str(v))
        self.__layout["scoreTable"].update(self.__scoresTable)

    def generateCombinationsTableData(self, combinations):
        self.__layout["combinationsTable"].update("")
        self.__combinationsTable = self.__createCombinationsTable()
        for idx, (k, v) in enumerate(combinations):
            self.__combinationsTable.add_row(
                str(idx), str(cfg.combinationsList.get(k)), str(v))

        self.__layout["combinationsTable"].update(self.__combinationsTable)

    def showInterface(self):
        # cls()
        self.__console.print(self.__layout)

    def clearErrorPanel(self):
        self.__layout["errors"].update(Panel("", title="Errors", style="red"))

    def resetDicesTable(self):
        self.__dicesTable = Table(title="Dices", box=box.ROUNDED)
        self.__dicesTable.add_column(
            "Dice", justify="right", style="cyan", no_wrap=True)
        self.__dicesTable.add_column("Result", style="white", justify="center")
