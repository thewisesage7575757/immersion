import discord
from discord.ext import commands
import json
import os.path
from os import remove
from datetime import datetime, date

class LoggingSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.masterPointsJson = "loggingSystem\\master\\masterPoints"
        self.thisMonthPointsJson = "loggingSystem\\monthPoints\\" + str(date.today())[:7]
        self.masterLogsJson = "loggingSystem\\master\\logs"
        print(f"{self.bot.user} is online!")
        print(f"{self.checkIfFileExist(self.masterPointsJson)} {self.checkIfFileExist(self.thisMonthPointsJson)} {self.checkIfFileExist(self.masterLogsJson)}")
        self.validMedia = [
            "anime", 
            "vn", 
            "ln", 
            "reading", 
            "listening", 
            "yt", 
            "readtime"]
        self.mediaUnit = {
            "anime" : "episode", 
            "vn" : "character", 
            "ln" : "character", 
            "reading" : "character", 
            "listening" : "minute", 
            "yt" : "minute", 
            "readtime" : "minute"}
        self.pointSystem = {
            "anime" : 3100, 
            "vn" : 1, 
            "ln" : 1, 
            "reading" : 1, 
            "listening" : 170, 
            "yt" : 170, 
            "readtime" : 170}
        
        if not self.checkIfFileExist(self.masterPointsJson):
            self.makeNewJson(self.masterPointsJson)
        if not self.checkIfFileExist(self.thisMonthPointsJson):
            self.makeNewJson(self.thisMonthPointsJson)
        if not self.checkIfFileExist(self.masterLogsJson):
            self.makeNewJson(self.masterLogsJson)
        
        self.log.description = "Adds your immersion to the database!\nValid mediaType for this are anime, vn, ln, reading, listening, yt, readtime\nUnits: anime - episodes, vn | ln | reading - characters, yt | listening | readtime - minutes"
        self.undo.description = "Removes your last log or a log of your choice\nIf you want to remove a previous log then do the logs command first and then copy down the date of the log you want to remove"
        self.backfill.description = "If you forgot to add your immersion to a previous month or day then backfill it\n It is the same thing as log but make sure to add a date"
        self.leaderboard.description = "Get the leaderboard\nVlid mediaTypes for this are all, anime, vn, ln, reading, listening, yt, readtime"
        self.logs.description = "Returns a file of your logs in json format"
        self.profile.description = "Displays your profiles and your stats"
  
    @commands.command()
    async def log(self, ctx, mediaType : str, unit : float, *comment):
        print(f"{datetime.today()} - {ctx.author.display_name} - Log command called")
        self.refreshMonth()
        authorId = str(ctx.author.id)

        if mediaType not in self.validMedia:
            await ctx.send(f"{mediaType} is not a valid media type")
            return
        if unit <= 0 or unit >= 2000000:
            await ctx.send(f"{ctx.author.mention} you are dumb. You can't log {unit} {mediaType} {self.makePlural(self.mediaUnit[mediaType], unit)}")
            return

        self.addNewIdToSystem(authorId)
        previousValues = self.fetchDoubleStats(authorId, mediaType)
        self.updatePoints(authorId, mediaType, unit, self.thisMonthPointsJson, False)
        self.createLog(authorId, mediaType, unit, " ".join(comment))
        presentValues = self.fetchDoubleStats(authorId, mediaType)
        await ctx.send(embed=self.makeLogEmbed(previousValues, presentValues, mediaType, unit, ctx.author))

    
    @commands.command()
    async def undo(self, ctx, *dateTime):
        print(f"{datetime.today()} - {ctx.author.display_name} - undo command called")
        self.refreshMonth()
        authorId = str(ctx.author.id)
        if len(dateTime) > 1:
            await ctx.send("Please only have 1 argument")
            return
        self.addNewIdToSystem(authorId)
        
        if len(dateTime) == 1:
            if self.fetchLog(authorId, dateTime[0])[0] == -1:
                await ctx.send(f"I could not find a log with the time at {dateTime[0]}.")
                return
            wholeLog = self.fetchLog(authorId, dateTime[0])
            log = wholeLog[1]
            previousValues = self.fetchDoubleStats(authorId, log["mediaType"], dateTime[0][:7])
            self.updatePoints(authorId, log["mediaType"], log["unit"], "loggingSystem\\monthPoints\\" + dateTime[0][:7], True)
            presentValues = self.fetchDoubleStats(authorId, log["mediaType"], dateTime[0][:7])
            self.removeLog(authorId, dateTime[0], wholeLog[0])
            await ctx.send(embed=self.makeUndoEmbed(previousValues, presentValues, log["mediaType"], log["unit"], ctx.author, "Month " + dateTime[0][:7]))
            return
        else:
            if self.fetchLastLog(authorId)[0] == -1:
                await ctx.send(f"You have to log first if you want to undo a log.")
                return
            log = self.fetchLastLog(authorId)[1]
            previousValues = self.fetchDoubleStats(authorId, log["mediaType"])
            self.updatePoints(authorId, log["mediaType"], log["unit"], self.thisMonthPointsJson, True)
            presentValues = self.fetchDoubleStats(authorId, log["mediaType"])
            self.removeLog(authorId)
            await ctx.send(embed=self.makeUndoEmbed(previousValues, presentValues, log["mediaType"], log["unit"], ctx.author, "This Month"))
            return  


    @commands.command()
    async def backfill(self, ctx, mediaType : str, unit : float, datein : str, *comment):
        print(f"{date.today()} - {ctx.author.display_name} - Log command called")
        self.refreshMonth()
        authorId = str(ctx.author.id)
        if mediaType not in self.validMedia:
            await ctx.send(f"{mediaType} is not a valid media type")
            return
        if unit <= 0 or unit >= 2000000:
            await ctx.send(f"{ctx.author.mention} you are dumb. You can't log {unit} {mediaType} {self.makePlural(self.mediaUnit[mediaType], unit)}")
            return
        if not self.checkIfFileExist("loggingSystem\\monthPoints\\" + datein[:7]):
            await ctx.send(f"I could not find a file with the month of {datein[:7]}")
            return
        if not self.checkIfIdExist(authorId, "loggingSystem\\monthPoints\\" + datein[:7]):
            self.addNewId("loggingSystem\\monthPoints\\" + datein[:7], authorId, False)
        previousValues = self.fetchDoubleStats(authorId, mediaType, datein[:7])
        self.updatePoints(authorId, mediaType, unit, "loggingSystem\\monthPoints\\" + datein[:7], False)
        self.createLog(authorId, mediaType, unit, " ".join(comment), datein)
        presentValues = self.fetchDoubleStats(authorId, mediaType, datein[:7])
        await ctx.send(embed=self.makeBackFillEmbed(previousValues, presentValues, mediaType, unit, ctx.author, datein[:7]))
        return
    
    @commands.command()
    async def leaderboard(self, ctx, mediaType, dateIn = None):
        print(f"{datetime.today()} - {ctx.author.display_name} - leaderboard command called")
        self.refreshMonth()
        if mediaType not in self.validMedia and mediaType != "all":
            await ctx.send("Please input a valid media type.")
            return
        if dateIn is None:
            leaderboardList = self.getLeaderboard(self.thisMonthPointsJson, mediaType)
            await ctx.send(embed= self.makeLeaderboardEmbed(leaderboardList, mediaType, str(date.today())[:7]))
            return
        if dateIn == "all":
            leaderboardList = self.getLeaderboard(self.masterPointsJson, mediaType)
            await ctx.send(embed= self.makeLeaderboardEmbed(leaderboardList, mediaType, "All Time"))
            return
        if not self.checkIfFileExist("loggingSystem\\monthPoints\\" + dateIn):
            await ctx.send(f"I could not find the month of {dateIn}.")
            return
        leaderboardList = self.getLeaderboard("loggingSystem\\monthPoints\\" + dateIn, mediaType)
        await ctx.send(embed= self.makeLeaderboardEmbed(leaderboardList, mediaType, dateIn))
        return
    
    @commands.command()
    async def logs(self, ctx):
        print(f"{datetime.today()} - {ctx.author.display_name} - logs command called")
        self.refreshMonth()
        authorId = str(ctx.author.id)
        authorName = ctx.author.display_name
        self.addNewIdToSystem(authorId)
        with open (self.masterLogsJson + ".json", "r") as f:
            data = json.load(f)
        data = data[authorId]
        with open (authorName + "Logs.txt", "w", encoding='utf8') as f:
            for log in data:
                f.write(f"{log['date'] : <20} | {log['mediaType'] : ^14} | {log['unit'] : ^10} | {log['comment']}\n")
        await ctx.send(file=discord.File(authorName + "Logs.txt"))
        os.remove(authorName + "Logs.txt")
        return

    @commands.command()
    async def profile(self, ctx, dateIn = "all"):
        print(f"{datetime.today()} - {ctx.author.display_name} - profile command called")  
        self.refreshMonth()  
        authorId = str(ctx.author.id)
        self.addNewIdToSystem(authorId)
        if not self.checkIfFileExist("loggingSystem\\monthPoints\\" + dateIn) and dateIn != "all":
            await ctx.send(f"I could not find a file with the month of {dateIn}.")
            return
        if not dateIn == "all" and not self.checkIfIdExist(authorId, "loggingSystem\\monthPoints\\" + dateIn):
            await ctx.send(f"I don't have any information on you in the month of {dateIn}.")
            return
        await ctx.send(embed= self.makeProfileEmbed(ctx.author, dateIn))
        return
    
    @log.error
    async def log_error(self, ctx, error):
        print(f"\nlog_error \n{error}")
        await ctx.send("This is how you do it: **i$log `mediaType` `number` `(optional)comments`**")
        return

    @undo.error
    async def undo_error(self, ctx, error):
        print(f"\nundo_error \n{error}")
        await ctx.send("This is how you do it: **i$undo `(optional)date and time`**")
        return

    @backfill.error
    async def backfill_error(self, ctx, error):
        print(f"\nbackfill_error \n{error}")
        await ctx.send("This is how you do it: **i$backfill `mediaType` `number` `date and time` `(optional)comments`**")
        return

    @leaderboard.error
    async def leaderboard_error(self, ctx, error):
        print(f"\nleaderboard_error \n{error}")
        await ctx.send("This is how you do it: **i$leaderboard `mediaType` `(optional) month (YYYY-MM)`**")
        return

    @logs.error
    async def logs_error(self, ctx, error):
        print(f"\nlogs_error \n{error}")
        await ctx.send("This is how you do it: **i$logs**")
        return

    @profile.error
    async def profile_error(self, ctx, error):
        print(f"\nprofile_error \n{error}")
        await ctx.send("This is how you do it: **i$profile `(optional) month (YYYY-MM)`")
        return

    def refreshMonth(self):
        self.thisMonthPointsJson = "loggingSystem\\monthPoints\\" + str(date.today())[:7]

    def fetchLastLog(self, id):
        with open(self.masterLogsJson + ".json", "r") as f:
            data = json.load(f)
        if len(data[id]) == 0:
            return -1, {}
        return len(data) - 1, data[id][len(data[id]) - 1]

    def fetchLog(self, id, date):
        with open(self.masterLogsJson + ".json", "r") as f:
            data = json.load(f)
        for i, log in enumerate(data[id]):
            if log["date"] == date:
                return i, log
        return -1, {}
    
    def fetchDoubleStats(self, id, mediaType, dateIn = "this"):
        return {"month" : self.fetchSingleStat(id, mediaType, self.thisMonthPointsJson if dateIn == "this" else "loggingSystem\\monthPoints\\" + dateIn), "all" : self.fetchSingleStat(id, mediaType, self.masterPointsJson)}
    
    def makeLogEmbed(self, previousValues, presentValues, mediaType, unit, user):
        logEmbed = discord.Embed(
            title= f"{mediaType.capitalize()} Log",
            description= f"{user.display_name} logged {unit} {self.makePlural(self.mediaUnit[mediaType], unit)}!",
            colour=0xffcbc0
        )
        logEmbed.add_field(
            name= f"This Month",
            value= f'{previousValues["month"]} -> {presentValues["month"]}\n{previousValues["month"]/self.pointSystem[mediaType]} {self.makePlural(self.mediaUnit[mediaType], previousValues["month"]/self.pointSystem[mediaType])} -> {presentValues["month"]/self.pointSystem[mediaType]} {self.makePlural(self.mediaUnit[mediaType], presentValues["month"]/self.pointSystem[mediaType])}',
            inline= True
        )
        logEmbed.add_field(
            name= "    ",
            value= "    ",
            inline= True
        )
        logEmbed.add_field(
            name= f"All Time",
            value= f'{previousValues["all"]} -> {presentValues["all"]}\n{previousValues["all"]/self.pointSystem[mediaType]} {self.makePlural(self.mediaUnit[mediaType], previousValues["all"]/self.pointSystem[mediaType])} -> {presentValues["all"]/self.pointSystem[mediaType]} {self.makePlural(self.mediaUnit[mediaType], presentValues["all"]/self.pointSystem[mediaType])}',
            inline= True
        )
        logEmbed.set_thumbnail(url=user.display_avatar.url)
        return logEmbed
    
    def makeUndoEmbed(self, previousValues, presentValues, mediaType, unit, user, month):
        logEmbed = discord.Embed(
            title= f"Removed Log",
            description= f"{user.display_name} removed {unit} {self.makePlural(self.mediaUnit[mediaType], unit)}!",
            colour=0xffcbc0
        )
        logEmbed.add_field(
            name= f"{month}",
            value= f'{previousValues["month"]} -> {presentValues["month"]}',
            inline= True
        )
        logEmbed.add_field(
            name= "    ",
            value= "    ",
            inline= True
        )
        logEmbed.add_field(
            name= f"All Time",
            value= f'{previousValues["all"]} -> {presentValues["all"]}',
            inline= True
        )
        logEmbed.set_thumbnail(url=user.display_avatar.url)
        return logEmbed
    
    def makeLeaderboardEmbed(self, data, mediaType, date):
        leaderboardEmbed = discord.Embed(
            title= f'{date} {mediaType.capitalize() if mediaType != "all" else ""} Leaderboard',
            description= f"Here are the top {len(data)}!",
            colour=0xffcbc0
        )
        for i, account in enumerate(data):
            user = self.bot.get_user(int(account[0]))
            leaderboardEmbed.add_field(
                name= f"{i + 1}. {user.display_name}  {account[1][mediaType]}",
                value= "",
                inline= False
            )
        if len(data) != 0:
            leaderboardEmbed.set_thumbnail(url= self.bot.get_user(int(data[0][0])).avatar.url)
        return leaderboardEmbed
    
    def makeBackFillEmbed(self, previousValues, presentValues, mediaType, unit, user, month):
        backfillEmbed = discord.Embed(
            title= f"{mediaType.capitalize()} Backfill",
            description= f"{user.display_name} backfilled {unit} {self.makePlural(self.mediaUnit[mediaType], unit)}!",
            colour=0xffcbc0
        )
        backfillEmbed.add_field(
            name= f"{month}",
            value= f'{previousValues["month"]} -> {presentValues["month"]}',
            inline= True
        )
        backfillEmbed.add_field(
            name= "    ",
            value= "    ",
            inline= True
        )
        backfillEmbed.add_field(
            name= f"All Time",
            value= f'{previousValues["all"]} -> {presentValues["all"]}',
            inline= True
        )
        backfillEmbed.set_thumbnail(url=user.display_avatar.url)
        return backfillEmbed

    def makeProfileEmbed(self, user, month):
        userId = str(user.id)
        data = self.fetchStats(userId, self.masterPointsJson if month == "all" else "loggingSystem\\monthPoints\\" + month).items()
        profileEmbed = discord.Embed(
            title=f'{user.display_name}\'s Profile {month if month != "all" else "All Time"}',
            description= "",
            colour=0xffcbc0
        )
        for media, stat in data:
            profileEmbed.add_field(
                name= f"{media.capitalize()}",
                value= f"**{stat}**",
                inline=False
            )
        profileEmbed.set_thumbnail(url= user.display_avatar.url)
        return profileEmbed

    def fetchSingleStat(self, id, mediaType, filename):
        with open (filename + ".json", "r") as f:
            data = json.load(f)
        return data[id][mediaType]
    
    def fetchStats(self, id, filename):
        with open (filename + ".json", "r") as f:
            data = json.load(f)
        return data[id]

    def addNewIdToSystem(self, id):
        if not self.checkIfIdExist(id, self.masterPointsJson):
            self.addNewId(self.masterPointsJson, id, False)
        if not self.checkIfIdExist(id, self.thisMonthPointsJson):
            self.addNewId(self.thisMonthPointsJson, id, False)
        if not self.checkIfIdExist(id, self.masterLogsJson):
            self.addNewId(self.masterLogsJson, id, True)

    def addNewId(self, filename, id, logs):
        with open (filename + ".json", "r") as f:
            data = json.load(f)

        if logs:
            data.update({id : []})
        else:
            data.update({id : {"all" : 0, "yt": 0, "listening": 0, "anime": 0, "vn": 0, "ln": 0, "reading": 0, "readtime" : 0}})
        
        with open (filename + ".json", "w") as f:
            json.dump(data, f, indent=2)

    def updatePoints(self, id, mediaType, unit, monthFile, remove):
        x = -1 if remove else 1
        with open (self.masterPointsJson + ".json", "r") as f, open (monthFile + ".json", "r") as g:
            masterPoints = json.load(f)
            thisMonthPoints = json.load(g)
        masterPoints[id][mediaType] += unit * self.pointSystem[mediaType] * x
        thisMonthPoints[id][mediaType] += unit * self.pointSystem[mediaType] * x
        masterPoints[id]["all"] += unit * self.pointSystem[mediaType] * x
        thisMonthPoints[id]["all"] += unit * self.pointSystem[mediaType] * x
        with open (self.masterPointsJson + ".json", "w") as f, open (monthFile + ".json", "w") as g:
            json.dump(masterPoints, f, indent=2)
            json.dump(thisMonthPoints, g, indent=2)
    
    def createLog(self, id, mediaType, unit, comment, dateIn = datetime.today().strftime("%Y-%m-%d-%H:%M")):
        with open (self.masterLogsJson + ".json", "r") as f:
            data = json.load(f)
        data[id].append({"date" : dateIn, "mediaType" : mediaType, "unit" : unit, "comment" : comment})
        with open (self.masterLogsJson + ".json", "w") as f:
            json.dump(data, f, indent=2)

    def removeLog(self, id, dateTime = None, index = None):
        with open (self.masterLogsJson + ".json", "r") as f:
            data = json.load(f)
        if dateTime is None:
            data[id].pop(len(data[id]) - 1)
        else:
            data[id].pop(index)
        with open (self.masterLogsJson + ".json", "w") as f:
            json.dump(data, f, indent=2)
        
    def makePlural(self, mediaType, unit):
        return mediaType if unit == 1 or unit == -1 else mediaType + "s"

    def checkIfIdExist(self, id, filename):
        with open (filename + ".json", "r") as f:
            data = json.load(f)
        return id in data

    def checkIfFileExist(self, filename):
        return os.path.exists(filename + ".json")
    
    def makeNewJson(self, filename):
        with open (filename + ".json", "w") as f:
            json.dump({}, f, indent=2)

    def getLeaderboard(self, filename, mediaType):
        with open (filename + ".json", "r") as f:
            data = json.load(f)
        data = data.items()
        data = sorted(data, key=lambda x: x[1][mediaType], reverse=True)
        numberOfLogs = 10 if len(data) > 9 else len(data)
        return [data[i] for i in range(numberOfLogs)]

async def setup(bot):
    await bot.add_cog(LoggingSystem(bot))