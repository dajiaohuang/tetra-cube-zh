var backgrounds, books, cardsources, classes, life, names, npcs, other, races,
    character = {}, prevCharacters = [],
    characterType = "either",
    usedBooks = [],
    mcEthnicity = "",
    ethnicityOption = "",
    defaultRaceSectionClass,
    lock = {
        "name": false,
        "traits": false,
        "occupation": false,
        "race": false,
        "class": false,
        "background": false,
        "life": false,
        "all": ["name", "traits", "occupation", "gender", "race", "class", "background", "life"]
    };

// Populate the 拖放downs with material from the selected books
var 拖放downs = {
    Update: function () {
        BookFunctions.Get();
        $("#racemenu").html(this.Get拖放downOptions(races));
        $("#classmenu").html(this.Get拖放downOptions(classes));
        $("#backgroundmenu").html(this.Get拖放downOptions(backgrounds));
    },

    Get拖放downOptions: function (list) {
        let optionsArray = ["<option value=\"Random\">Random</option>"];
        for (let propertyName in list) {
            let item = list[propertyName];
            if (typeof item != "object" || !item.hasOwnProperty("_special") || BookFunctions.CheckSpecial(item._special))
                optionsArray.push("<option value=\"" + propertyName + "\">" + propertyName + "</option>");
        }
        return optionsArray.join("");
    },
}

// Get or check what books we have
var BookFunctions = {
    // Get the books we have from the checkboxes
    Get: function () {
        usedBooks = ["Real", "PHB"];
        for (let bookNum = 0; bookNum < books.availableBooks.length; bookNum++) {
            let book = books.availableBooks[bookNum];
            if ($("#" + book + "box").prop("checked"))
                usedBooks.push(book);
        }
    },

    // Check an entire _special string
    CheckSpecial: function (specialString) {
        let splitSpecial = specialString.split(" ");
        for (let specialIndex = 0; specialIndex < splitSpecial.length; specialIndex++) {
            if (splitSpecial[specialIndex].slice(0, 5) == "book-")
                return this.CheckString(splitSpecial[specialIndex].slice(5));
        }
        return false;
    },

    // Check a string of only books
    CheckString: function (bookString) {
        for (let index = 0; index < usedBooks.length; index++) {
            if (bookString.includes(usedBooks[index]))
                return true;
        }
        return false;
    }
}

var CharacterType = {
    GetNoCard: function () {
        characterType = $("#pc-radio").prop("checked") ? "pc" : $("#npc-radio").prop("checked") ? "npc" : "either";
        if (characterType == "pc") {
            $(".pc-show, .pc-only-show").show();
            $(".npc-show, .npc-only-show").hide();
            $("#race-section").prop("class", defaultRaceSectionClass);
            $("#name-lock-div").removeClass("col-lg-4");
        } else if (characterType == "npc") {
            $(".npc-show, .npc-only-show").show();
            $(".pc-show, .pc-only-show").hide();
            $("#race-section").prop("class", "col-12");
            $("#name-lock-div").addClass("col-lg-4");
        } else {
            $(".pc-show, .npc-show").show();
            $(".pc-only-show, .npc-only-show").hide();
            $("#race-section").prop("class", defaultRaceSectionClass);
            $("#name-lock-div").addClass("col-lg-4");
        }
    },
    Get: function () {
        this.GetNoCard();
        CardType.Set();
    }
}

// For when the user clicks one of the Generate buttons, or when the page loads
var Generate = {
    All: function () {
        BookFunctions.Get();

        this.Race();
        this.Gender();
        this.Class();
        this.Background();
        this.Occupation();
        this.NPCTraits();
        this.Life();

        this.FinishGenerate();
    },

    Race: function () {
        if (lock.race) return;
        // Determine human ethnicity
        ethnicityOption = $("#standard-radio").prop("checked") ? "standard" :
            $("#real-radio").prop("checked") ? "real" :
                Random.Array(["standard", "real"]);

        // Determine race weight
        let raceVal = $("#racemenu").val();
        character.Race = Content.GetRandom(races, raceVal == "Random" ?
            $("#weighted-radio").prop("checked") ? RaceWeighted.Get() :
                $("#15x-weighted-radio").prop("checked") ? RaceWeighted.Get(1.5) :
                    $("#20x-weighted-radio").prop("checked") ? RaceWeighted.Get(2) :
                        "Random" : raceVal);
    },

    Gender: function () {
        let genderVal = $("#gendermenu").val();
        character.Gender = (genderVal == "Random" ? Random.Array(other.genders) : genderVal);

        this.Name();
    },

    Name: function () {
        let nameVal = $("#name-input").val();
        if (nameVal.length == 0) {
            character.Name = Names.Get(character.Race.name, character.Gender);
            character.ShortName = Names.Shortened();
        }
        else {
            character.Name = nameVal;
            character.ShortName = nameVal;
        }
    },

    Class: function () {
        if (lock.class) return;
        character.Class = Content.GetRandom(classes, $("#classmenu").val());
    },

    Background: function () {
        if (lock.background) return;
        character.Background = Content.GetRandom(backgrounds, $("#backgroundmenu").val());
    },

    Occupation: function () {
        if (lock.occupation) return;
        character.Occupation = Occupation.Get();
    },

    NPCTraits: function () {
        if (lock.traits) return;
        character.NPCTraits = {
            "name": "NPCTraits",
            "content": Content.Get(NPCTraits.Get())
        };
    },

    Life: function () {
        if (lock.life) return;
        character.Life = {
            "name": "Life",
            "content": Content.Get(Life.Get())
        };
    },

    // Functions for when a specific button is pressed

    RaceInput: function () {
        BookFunctions.Get();
        this.Race();
        this.Name();
        this.Life();
        CardType.Set();
        this.FinishGenerate();
    },

    GenderInput: function () {
        this.Gender();
        this.FinishGenerate();
    },

    NameInput: function () {
        BookFunctions.Get();
        this.Name();
        this.FinishGenerate();
    },

    ClassInput: function () {
        BookFunctions.Get();
        this.Class();
        this.FinishGenerate();
    },

    BackgroundInput: function () {
        BookFunctions.Get();
        this.Background();
        this.FinishGenerate();
    },

    OccupationInput: function () {
        BookFunctions.Get();
        this.Occupation();
        this.FinishGenerate();
    },

    NPCTraitsInput: function () {
        BookFunctions.Get();
        this.NPCTraits();
        this.FinishGenerate();
    },

    LifeInput: function () {
        BookFunctions.Get();
        this.Life();
        this.FinishGenerate();
    },

    FinishGenerate: function () {
        CardType.Set();
        Characters.SaveCharacter();
        Characters.SaveToStorage();
        SetHTML();
    }
}

function SetHTML() {

    $("#name").html(character.Name);

    $("#race, #raceheader").html(character.Race.name);
    $("#racesection").html(HTMLStrings.Get(character.Race));

    $("#gender, #genderheader").html(character.Race.name == "战俑" ? "无性别" : character.Gender);

    $("#class, #classheader").html(character.Class.name);
    $("#classsection").html(HTMLStrings.Get(character.Class));

    $("#background, #backgroundheader").html(character.Background.name);
    $("#backgroundsection").html(HTMLStrings.Get(character.Background));

    $("#occupation").html(character.Occupation);

    $("#npc-traits-section").html(HTMLStrings.Get(character.NPCTraits));

    $("#lifesection").html(HTMLStrings.Get(character.Life));
}

// Gets content from dnd-data and puts it into a format more readable to the generator (also filters out things that should be inaccessible)
var Content = {
    // Set all properties in an object
    Get: function (item) {
        if (item == null) return null;
        if (typeof item == "object") {
            if (Array.isArray(item))
                return this.Get(Random.Array(item));
            else {
                if (item.hasOwnProperty("_special")) {
                    let specialItem = this.Special(item);
                    if (jQuery.isEmptyObject(specialItem))
                        return null;
                    return specialItem;
                }
                let properties = [];
                for (let propertyName in item) {
                    let content = this.Get(item[propertyName]);
                    if (content != null)
                        properties.push({
                            "name": propertyName,
                            "content": content
                        });
                }
                return properties;
            }
        }
        return item;
    },

    // Get a random property from an initial object
    GetRandom: function (item, 拖放downVal = "Random") {
        if (拖放downVal != "Random")
            return {
                "name": 拖放downVal,
                "content": this.Special(item[拖放downVal])
            };
        let propsArr = [],
            randomProp;
        for (let propName in item) {
            if (item[propName].hasOwnProperty("_special") && BookFunctions.CheckSpecial(item[propName]._special))
                propsArr.push(propName);
        }
        randomProp = Random.Array(propsArr);
        return {
            "name": randomProp,
            "content": this.Special(item[randomProp])
        };
    },


    // For dealing with special cases (indicated by the _special keyword)

    Special: function (item) {
        // Clone the item, remove special from the clone, and apply every special in order
        let newItem = Object.assign({}, item),
            cases = item._special.split(" ");
        delete newItem._special;
        for (let caseIndex = 0; caseIndex < cases.length; caseIndex++)
            newItem = this.ApplySpecial(cases[caseIndex], newItem);
        if (jQuery.isEmptyObject(newItem))
            return null;
        return this.Get(newItem);
    },

    ApplySpecial: function (special, specialItem) // Apply one special case to an object and return the resulting object
    {
        if (specialItem == null || typeof specialItem != "object") return specialItem;
        let splitSpecial = special.split("-");

        switch (splitSpecial[0]) {
            case "book": // Remove this item if we don''t have the necessary book't have. Then pick randomly from it.
                return this.BookSort(specialItem);

            case "characteristics": // Output height, weight, appearance, etc
                return this.GetCharacteristics(specialItem);

            case "gendersort": // Get property according to gender
                return character.Gender == "男性" ? specialItem.男性 :
                    character.Gender == "女性" ? specialItem.女性 :
                        Random.Array([specialItem.男性, specialItem.女性]);

            case "halfethnicity": // Get human ethnicity for half-humans
                mcEthnicity = (Random.Num(5) > 0 ? RandomEthnicity.Get() : "Unknown");
                return mcEthnicity;

            case "humanethnicity": // Get human ethnicity for full-humans
                mcEthnicity = RandomEthnicity.Get();
                return mcEthnicity;

            case "subracesort": // For certain races, we need to know the subrace to determine the 身体特征. This is less hacky than the code it replaced.
                let SubracePropName = (splitSpecial.length > 1 ? (splitSpecial[1].split("_").join(" ")) : "子种族"),
                    subracesAndVariants = specialItem["子种族与变体"],
                    newSubVar = {},
                    subraceString;

                for (let propertyName in subracesAndVariants) {
                    if (propertyName == SubracePropName) {
                        subraceString = Array.isArray(subracesAndVariants[propertyName]) ?
                            Random.Array(subracesAndVariants[SubracePropName]) :
                            this.BookSort(subracesAndVariants[SubracePropName]);
                        newSubVar[propertyName] = subraceString;
                    } else
                        newSubVar[propertyName] = subracesAndVariants[propertyName];
                }
                // specialItem["子种族与变体"] = newSubVar;
                // specialItem["身体特征"] = specialItem["身体特征"][subraceString];
                return {
                    "子种族与变体": newSubVar,
                    "身体特征": specialItem["身体特征"][subraceString]
                };

            case "dragonbornvarianttype": // Wildemount dragonborn have weird variants
                if (!usedBooks.includes("EGtW"))
                    return null;
                return Random.Array(specialItem._array);

            case "dragonmarkvariant": // Eberron dragonmarks
                if (!usedBooks.includes("EBR") || Random.Num(2) == 0)
                    return null;
                return Random.Array(specialItem._array);

            case "tieflingappearance": // Tieflings have weird appearances
                if (Random.Num(3) == 0)
                    return null;
                return Random.ArrayMultiple(specialItem._array, Random.DiceRoll("1d4") + 1);

            case "tieflingvarianttype": // Tieflings also have weird variants
                if (!usedBooks.includes("SCAG"))
                    return null;
                return Random.Array(specialItem._array);

            case "monstrousorigin": // 怪物 origins
                return Random.Array(other.monstrousOrigins);

            case "backgroundtraits": // For the SCAG backgrounds where the writers were lazy and used personalities from the PHB 
                let backgroundCopy = backgrounds[splitSpecial[1].split("_").join(" ")];
                // specialItem["特质"] = backgroundCopy.特质;
                // specialItem["理念"] = backgroundCopy.理念;
                // specialItem["羁绊"] = backgroundCopy.羁绊;
                // specialItem["缺陷"] = backgroundCopy.缺陷;
                return {
                    "特质": backgroundCopy.特质,
                    "理念": backgroundCopy.理念,
                    "羁绊": backgroundCopy.羁绊,
                    "缺陷": backgroundCopy.缺陷
                };

            case "ravnicacontacts": // Ravnica 背景
                let guildName = specialItem["_name"],
                    ravnicaContacts = {};
                ravnicaContacts[guildName + " Ally"] = Random.Array(specialItem["_guild"]);
                ravnicaContacts[guildName + " Rival"] = Random.Array(specialItem["_guild"]);
                let nonGuildContact = Random.Array(specialItem["_nonguild"]);
                if (nonGuildContact == "_reroll") {
                    nonGuildContact = Random.Array(specialItem["_guild"]);
                    ravnicaContacts["Additional " + guildName + " Contact"] = nonGuildContact
                }
                else
                    ravnicaContacts["Non-" + guildName + " Contact"] = nonGuildContact;
                return ravnicaContacts;

            case "dimircontacts": // Ravnica 背景, House Dimir is a special case
                let dimirContacts = {}, secondaryGuild = Random.Array(specialItem._guilds),
                    otherGuildContacts = backgrounds[secondaryGuild.background]["联系"]["_guild"];
                dimirContacts[""Dimir盟友""] = Random.Array(specialItem["_dimircontact"]);
                dimirContacts[""次级公会""] = secondaryGuild.name;
                dimirContacts[""次要公会盟友""] = Random.Array(otherGuildContacts);
                dimirContacts[""次要公会对手""] = Random.Array(otherGuildContacts);
                return dimirContacts;
            //"“额外掷一次阿佐里乌斯联系人的骰子；你可以决定这个联系人是盟友还是对手。”",
        }
        return specialItem;
    },

    // Remove every array that'不适用，因为我们没有't have the book, then merge the remaining arrays and pick randomly from them
    BookSort: function (specialItem) {
        if (specialItem.hasOwnProperty("_special"))
            delete specialItem._special;
        let contentArr = [];
        for (let bookName in specialItem) {
            if (BookFunctions.CheckString(bookName))
                contentArr = contentArr.concat(specialItem[bookName]);
        }
        return Random.Array(contentArr);
    },

    // Compute age, height, weight, and other 身体特征
    GetCharacteristics: function (item) {
        let chaObj = {},
            age = Random.Num(item.maxage - item.minage) + item.minage;
        age += (age == "1" ? " year" : " years"); // Extremely rare edge case but it can happen
        chaObj.年龄 = age;

        let heightmod = Random.DiceRoll(item.heightmod),
            intHeight = item.baseheight + heightmod;
        chaObj.Height = Math.floor(intHeight / 12) + "'" + (intHeight % 12) + "\"";
        chaObj.Weight = item.baseweight + heightmod * Random.DiceRoll(item.weightmod) + " lbs.",
            otherObj = item._other;

        if (otherObj == undefined)
            return chaObj;
        for (let otherName in otherObj)
            chaObj[otherName] = otherObj[otherName];
        return chaObj;
    }
}

// Functions for random number/content selecting
var Random = {
    // Generate random number
    Num: function (max) {
        return Math.floor(Math.random() * max);
    },

    // Pick a random element from an array
    Array: function (arr) {
        return arr[this.Num(arr.length)];
    },

    // Pick multiple random elements from an array
    ArrayMultiple: function (arr, num) {
        let returnArray = [];
        while (returnArray.length < num) {
            let item = this.Array(arr);
            if (!returnArray.includes(item))
                returnArray.push(item);
        }
        return returnArray.join(", ");
    },

    // Roll dice 基于 a string (eg. '2d6')
    DiceRoll: function (roll) {
        numbers = roll.split("d");
        if (numbers.length == 1)
            return numbers[0];
        let total = 0;
        for (let die = 0; die < numbers[0]; die++)
            total += this.Num(numbers[1]) + 1;
        return total;
    },
}

// Functions for making content objects into HTML strings to be displayed
var HTMLStrings = {
    Get: function (item) {
        let itemContent = item.content,
            stringBuffer = [];
        for (let index = 0; index < itemContent.length; index++)
            stringBuffer.push(this.GetNext(itemContent[index]));
        return stringBuffer.join("");
    },

    GetNext: function (item) {
        let itemContent = item.content;
        if (typeof itemContent != "object")
            return "<li><b>" + item.name + "</b>: " + itemContent + "</li>";

        let stringBuffer = [];
        for (let index = 0; index < itemContent.length; index++)
            stringBuffer.push(this.GetNext(itemContent[index]));
        return "<li><b> " + item.name + "</b>:<ul>" + stringBuffer.join("") + "</ul></li>";
    },

    Life: function (item) {
        if (typeof item == "object") {
            let itemContent = item.content,
                stringBuffer = [];
            for (let propertyName in itemContent)
                stringBuffer.push(this.Life(itemContent[propertyName]));
            return stringBuffer.join("");
        }
        return item;
    },
}

// Functions relating to the character's name
var Names = {
    Get: function (raceName, gender) {
        switch (raceName) {
            case "鸟羽人":
            case "幻身灵":
            case "格龙蛙人":
            case "天狗":
            case "狗头人":
            case "蜥蜴人":
            case "洛卡鱼人":
            case "化兽者":
            case "龟人":
            case "佛丹人":
            case "战俑":
                return Random.Array(names[raceName]);

            case "熊地精":
            case "地精":
            case "大地精":
                return this.GetGendered(names["Goblinoid"], gender);

            case "人马":
            case "牛头人":
            case "兽人":
            case "狮族":
            case "象族":
            case "维多肯":
                return this.GetGendered(names[raceName], gender);

            case "阿斯莫":
            case "半血裔":
            case "元素裔":
            case "巫咒之子":
            case "重生者":
                return this.GetHuman(this.GetHumanEthnicity(), gender);

            case "龙裔":
                return this.FirstnameLastname(names.龙裔, "Clan", gender);

            case "矮人":
                if (this.GetSubrace() == "灰矮人")
                    return this.GetGendered(names.矮人, gender) + " " + Random.Array(names.矮人["Clan (灰矮人)"]);
                return this.FirstnameLastname(names.矮人, "Clan", gender);

            case "精灵":
                if (this.GetSubrace() == "卓尔")
                    return this.FirstnameLastname(names.卓尔, "Family", gender);
                if (this.GetSubrace() == "Shadar-kai")
                    return this.GetGendered(names["Shadar-kai"], gender);
                return character.age < 80 + Random.Num(40) ?
                    Random.Array(names.精灵.Child) + " " + Random.Array(names.精灵.Family) :
                    this.FirstnameLastname(names.精灵, "Family", gender);

            case "费尔伯格人":
                return this.GetGendered(names.精灵, gender);

            case "吉斯人":
                return this.GetSubrace() == "吉斯洋基人" ?
                    this.GetGendered(names.吉斯洋基人, gender) :
                    this.GetGendered(names.吉斯泽莱人, gender);

            case "侏儒":
                if (this.GetSubrace() == "地底侏儒")
                    return this.FirstnameLastname(names["地底侏儒"], "Clan", gender);
                let firstNames, numNames = 4 + Random.Num(4);
                let gnomeNames = [];
                while (gnomeNames.length < numNames) {
                    let item;
                    if (gender == "男性" || gender == "女性")
                        item = Random.Array(names.侏儒[gender]);
                    else
                        item = Random.Array(names.侏儒[this.RandomGender()]);
                    if (!gnomeNames.includes(item))
                        gnomeNames.push(item);
                }
                firstNames = gnomeNames.join(" ");
                return firstNames + " "" + Random.Array(names.侏儒.Nickname) + "" " + Random.Array(names.侏儒.Clan);

            case "歌利亚":
                return Random.Array(names.歌利亚.Birth) + " "" + Random.Array(names.歌利亚.Nickname) + "" " + Random.Array(names.歌利亚.Clan);

            case "半身人":
                return this.FirstnameLastname(names.半身人, "Family", gender);

            case "半精灵":
                let hElfRand = Random.Num(6),
                    elfSubrace = this.GetSubrace(),
                    elfNameArray =
                        elfSubrace == "卓尔" ? names.卓尔 : names.精灵;
                if (hElfRand < 2) return this.HumanFirst(this.GetHumanEthnicity(), gender) + " " + Random.Array(elfNameArray.Family); // 人类 First, 精灵 Last
                if (hElfRand < 4) return this.GetGendered(elfNameArray, gender) + this.HumanLast(this.GetHumanEthnicity()); // 精灵 first, 人类 Last
                if (hElfRand < 5) return this.GetHuman(this.GetHumanEthnicity(), gender); // Both 人类
                return this.FirstnameLastname(elfNameArray, "Family", gender); // Both 精灵

            case "半兽人":
                let hOrcRand = Random.Num(4);
                return hOrcRand < 1 ? this.GetGendered(names.兽人, gender) :
                    hOrcRand < 2 ? this.GetGendered(names.兽人, gender) + this.HumanLast(this.GetHumanEthnicity()) :
                        this.GetHuman(this.GetHumanEthnicity(), gender);

            case "人类":
                return this.GetHuman(mcEthnicity, gender);

            case "离梦人":
                return Random.Array(names["离梦人/Quori"]);

            case "狮族":
                return this.FirstnameLastname(names.狮族, "Pride", gender);

            case "半羊人":
                return this.GetGendered(names.半羊人, gender) + " "" + Random.Array(names.半羊人.Nicknames) + """;

            case "析米克混生体":
                let raceNames = Random.Array([names.人类, names.精灵, names.维多肯]);
                return raceNames == names.人类 ? this.GetHuman(RandomEthnicity.Get(), gender) : this.GetGendered(raceNames, gender);

            case "斑猫人":
                return Random.Array(names.斑猫人.Name) + " " + Random.Array(names.斑猫人.Clan);

            case "梭螺鱼人":
                return this.FirstnameLastname(names.梭螺鱼人, "Surname", gender);

            case "提夫林":
                if (Random.Num(5) < 2)
                    return this.GetHuman(this.GetHumanEthnicity(), gender);
                let lastName = this.HumanLast(this.GetHumanEthnicity());
                return gender == "男性" || gender == "女性" ?
                    Random.Num(3) == 0 ? this.GetGendered(names.炼狱语, gender) + lastName : Random.Array(names.Virtue) + lastName :
                    Random.Num(3) > 0 ? Random.Array(names.Virtue) + lastName : this.GetGendered(names.炼狱语, gender) + lastName;

            case "纯血原体蛇人":
                return Random.Array(names["蛇人"]);
        }
    },

    Shortened: function () {
        if (character.Race.name == "侏儒" && character.Race.content[0].content[0].content != "地底侏儒") {
            let nameArr = character.Name.split(" "),
                firstName = nameArr[Random.Num(nameArr.length - 2)];
            return firstName + " " + nameArr[nameArr.length - 2] + " " + nameArr[nameArr.length - 1];
        } else if (character.Race.name == "斑猫人") {
            let nicknameIndex = character.Name.indexOf(""");
            return character.Name.substring(nicknameIndex);
        }
        return character.Name;
    },

    RandomGender: () => Random.Array(["男性", "女性"]),

    GetSubrace: function () {
        let race = character.Race.content
        for (let index = 0; index < race.length; index++) {
            if (race[index].name == "子种族与变体") {
                let subrace = race[index].content;
                for (let index2 = 0; index2 < subrace.length; index2++) {
                    if (subrace[index2].name == "子种族")
                        return subrace[index2].content;
                }
            }
        }
    },

    // Return a gendered first name and a last name 基于 race
    FirstnameLastname: function (names, lastnameType, gender) {
        return this.GetGendered(names, gender) + " " + Random.Array(names[lastnameType]);
    },

    // Get the gender or a random generator if the character doesn't have one
    GetGendered: function (names, gender) {
        return Random.Array(names[(gender == "男性" || gender == "女性" ? gender : this.RandomGender())]);
    },

    // Get a human name
    GetHuman: function (ethnicity, gender) {
        let lastName = this.HumanLast(ethnicity);
        return this.HumanFirst(ethnicity, gender) + (lastName != null ? lastName : "");
    },

    HumanFirst: function (ethnicity, gender) {
        return ethnicityOption == "standard" ?
            this.GetGendered(ethnicity == "Tethyrian" ? names.人类.Chondathan : names.人类[ethnicity], gender) :
            this.GetGendered(names["人类 (Real)"][ethnicity], gender);
    },

    HumanLast: function (ethnicity) {
        return ethnicityOption == "standard" ?
            ethnicity == "Bedine" ? " " + Random.Array(names.人类.Bedine.Tribe) :
                ethnicity == "Tethyrian" ? " " + Random.Array(names.人类.Chondathan.Surname) :
                    (ethnicity == "Tuigan" || ethnicity == "Ulutiun") ? "" : " " + Random.Array(names.人类[ethnicity].Surname) : "";
    },

    // Get character's human heritage - for half-elves, half-orcs, tieflings, aasimar, and genasi
    GetHumanEthnicity: () => (mcEthnicity == "Unknown" ? RandomEthnicity.Get() : mcEthnicity),
}

// Determine race 基于 weighted probabilities (ie. more common races are more likely to come up)
var RaceWeighted = {
    Get: function (pow = 1) {
        let raceWeightList = [], totalWeight = 0;
        for (let raceName in other.raceWeights) {
            let weight = Math.pow(other.raceWeights[raceName], pow);
            raceWeightList[raceName] = weight;
            totalWeight += weight;
        }
        for (let raceName in races) {
            let race = races[raceName];
            if (race._special.includes("PHB") || !BookFunctions.CheckSpecial(race._special)) continue;
            raceWeightList[raceName] = 1;
            totalWeight += 1;
        }
        let rand = Random.Num(totalWeight);
        for (let race in raceWeightList) {
            rand -= raceWeightList[race];
            if (rand <= 0)
                return race;
        }
    }
}

// Oddball function for returning a random human ethnicity
var RandomEthnicity = {
    Get: function () {
        return ethnicityOption == "standard" ?
            usedBooks.includes("SCAG") ?
                Random.Array(races.人类["子种族与变体"].Ethnicity.PHB.concat(races.人类["子种族与变体"].Ethnicity.SCAG)) :
                Random.Array(races.人类["子种族与变体"].Ethnicity.PHB) :
            Random.Array(races.人类["子种族与变体"].Ethnicity.Real);
    }
}

// Return random traits as given in the NPC section of the DMG
var NPCTraits = {
    Get: function () {
        let newNPCTraits = {
            "外表": Random.Array(npcs.appearances)
        },
            highTraitNum = Random.Num(npcs.highAbilities.length),
            lowTraitNum = Random.Num(npcs.lowAbilities.length - 1);

        // 低属性 can't be the same as the 高属性
        if (lowTraitNum >= highTraitNum)
            lowTraitNum++;

        newNPCTraits["高属性"] = npcs.highAbilities[highTraitNum];
        newNPCTraits["低属性"] = npcs.lowAbilities[lowTraitNum];

        newNPCTraits.天赋 = Random.Array(npcs.talents);
        newNPCTraits.习癖 = Random.Array(npcs.mannerisms);
        newNPCTraits["互动特质"] = Random.Array(npcs.interactionTraits);

        let ideal = Random.Array(npcs.ideals),
            bond, bond1 = Random.Num(10)
        if (bond1 < 9)
            bond = npcs.bonds[bond1];
        else {
            bond1 = Random.Num(9);
            let bond2 = Random.Num(9);
            while (bond2 == bond1)
                bond2 = Random.Num(9);
            bond = npcs.bonds[bond1] + ", " + npcs.bonds[bond2];
        }
        newNPCTraits.价值观 = ideal + ", " + bond;

        newNPCTraits["缺陷或秘密"] = Random.Array(npcs.flawsAndSecrets);
        return newNPCTraits;
    }
}

var Occupation = {
    Get: function (allowAdventurer) {
        let rand = Random.Num(allowAdventurer ? 100 : 99);
        return rand < 5 ? "学者" :
            rand < 10 ? "贵族" :
                rand < 25 ? "工匠或公会成员" :
                    rand < 30 ? "罪犯" :
                        rand < 35 ? "艺人" :
                            rand < 37 ? "流放者、隐士或难民" :
                                rand < 42 ? "探险者或流浪者" :
                                    rand < 54 ? "农夫或牧民" :
                                        rand < 59 ? "猎人或捕兽者" :
                                            rand < 74 ? "劳工" :
                                                rand < 79 ? "商人" :
                                                    rand < 84 ? "政客或官僚" :
                                                        rand < 89 ? "祭司" :
                                                            rand < 94 ? "水手" :
                                                                rand < 99 ? "士兵" :
                                                                    "冒险者 (" + Life.ClassWeighted() + ")";
    },
}

// Return random 人生事件 as given in Xanathar's guide
var Life = {
    Get: function () {
        let newLife = {};
        newLife.阵营 = Random.Array(life.alignments);
        newLife.出身 = {};
        if (character.Race.name == "战俑")
            newLife.出身.Built = Random.Array(life.origins.出生地);
        else
            newLife.出身.出生地 = Random.Array(life.origins.出生地);
        let parents = life.origins.父母[character.Race.name];
        if (parents != undefined)
            newLife.出身.父母 = Random.Array(parents);

        let raisedBy = this.RaisedBy();
        if (raisedBy != "母亲和父亲")
            newLife.出身["缺席的父母(s)"] = this.AbsentParent();

        let lifestyle = this.Lifestyle();
        newLife.出身["家庭生活方式"] = lifestyle[0];
        newLife.出身["童年住所"] = this.Home(lifestyle[1]);
        newLife.出身["童年记忆"] = this.Memories();

        newLife.出身["兄弟姐妹"] = this.兄弟姐妹(newLife.出身.父母);

        newLife["人生事件"] = this.LifeEvents();
        newLife["饰品"] = Random.Array(life.trinkets);

        return newLife;
    },

    LifeEvents: function () {
        let lifeEvents = {};
        let numEvents = 3 + Random.Num(3);
        for (let eventNum = 0; eventNum < numEvents; eventNum++) {
            let newEventType = "";
            do {
                let randomEventNum = Random.Num(100);
                newEventType = randomEventNum == 99 ? "奇事" :
                    life.eventTables["人生事件"][Math.floor(randomEventNum / 5)];
            } while (lifeEvents.hasOwnProperty([newEventType]))

            let newEvent = "";
            switch (newEventType) {
                case "婚姻":
                    let spouseRace;
                    if (Random.Num(3) < 2)
                        spouseRace = character.Race.name;
                    else
                        spouseRace = RaceWeighted.Get();
                    newEvent = ""你爱上或嫁给了一个(n)"" + spouseRace.toLowerCase() + " " + Occupation.Get(true).toLowerCase() + ".";
                    break;
                case "朋友":
                    newEvent = ""你和一个(n)成为了朋友"" + RaceWeighted.Get().toLowerCase() + " " + this.ClassWeighted().toLowerCase() + ".";
                    break;
                case "敌人":
                    newEvent = ""你与一名(n)结下了仇怨"" + RaceWeighted.Get().toLowerCase() + " " + this.ClassWeighted().toLowerCase() + "". 投掷一枚d6。奇数表示你对裂痕负有责任，偶数则表示你是无辜的。"";
                    break;
                case "工作":
                    newEvent = ""你在与你的背景相关的工作中度过了一段时间。游戏开始时额外获得2d6金币。"";
                    break;
                case "重要之人":
                    newEvent = ""你遇到了一个重要的"" + RaceWeighted.Get().toLowerCase() + "", 是"" + this.Relationship().toLowerCase() + "向你移动。";
                    break;
                case "冒险":
                    let rand = Random.Num(100);
                    newEvent = rand == 99 ? life.eventTables.冒险[10] : life.eventTables.冒险[Math.floor(rand / 10)];
                    break;
                case "罪行":
                    newEvent = Random.Array(life.eventTables.罪行) + ". " + Random.Array(life.eventTables.Punishment);
                    break;
                default:
                    newEvent = Random.Array(life.eventTables[newEventType]);
                    break;
            }
            lifeEvents[newEventType] = newEvent;
        }
        return lifeEvents;
    },

    兄弟姐妹: function (parents) // Determine who our siblings are
    {
        let numSiblings = Random.Num(3);
        if (numSiblings == 0) return null;
        siblings = {};
        for (let sibNum = 0; sibNum < numSiblings; sibNum++) {
            let newSib = {},
                race = this.SiblingRace(parents);
            if (race != "战俑")
                newSib.Gender = Random.Array(other.genders);
            newSib.Race = race;
            newSibName = this.SiblingName(newSib);
            while (newSibName == character.Name.substring(0, newSibName.length))
                newSibName = this.SiblingName(newSib);
            newSib.阵营 = this.阵营();
            newSib.Occupation = Occupation.Get(true);
            newSib.Status = this.Status();

            newSib.Relationship = this.Relationship();

            let birthOrderRoll = Random.DiceRoll("2d6"),
                birthOrder;
            if (newSib.Race == "战俑") {
                birthOrder = birthOrderRoll < 3 ? "同时出生" :
                    birthOrderRoll < 8 ? "年长" : "年幼"
                newSib["制造顺序"] = birthOrder;
            } else {
                birthOrder = birthOrderRoll < 3 ? "双胞胎、三胞胎或四胞胎" :
                    birthOrderRoll < 8 ? "年长" : "年幼"
                newSib["出生顺序"] = birthOrder;
            }
            siblings[newSibName] = newSib;
        }
        return siblings;
    },

    SiblingRace: function (parents) // If mixed-race, determine races of siblings
    {
        switch (character.Race.name) {
            case "半精灵":
                return parents == "“其中一个父母是精灵，另一个是半精灵。”" ?
                    Random.Array(["精灵", "半精灵"]) :
                    parents == "“一位父母是人类，另一位是半精灵。”" ?
                        Random.Array(["人类", "半精灵"]) : "半精灵";
            case "半兽人":
                return parents == ""一个父母是兽人，另一个是半兽人。"" ?
                    Random.Array(["兽人", "半兽人"]) :
                    parents == "“一个父母是人类，另一个是半兽人。”" ?
                        Random.Array(["人类", "半兽人"]) : "半兽人";
            case "提夫林":
                return parents == ""两人都为人类，他们的恶魔血统在你出现之前一直沉睡着。"" ?
                    Random.Array(["人类", "人类", "人类", "提夫林"]) :
                    parents == "“一个父母是 提夫林，另一个是人类。”" ?
                        Random.Array(["人类", "提夫林"]) : "提夫林";
            case "元素裔":
                return parents == "“一个父母是基因精种，另一个是人类。”" ?
                    Random.Array(["人类", "元素裔"]) :
                    parents == "“父母都是人类，他们的元素血统在你出现之前一直沉睡。”" ?
                        Random.Array(["人类", "人类", "人类", "元素裔"]) : "元素裔";
            case "阿斯莫":
                return parents == ""双方父母都是人类，他们的天界血统在你出生时才显现。"" ?
                    "人类" : Random.Array(["人类", "阿斯莫"]);
        }
        return character.Race.name;
    },

    // Random tables

    SiblingName: function (sibling) {
        let siblingRace = sibling.Race,
            name;
        if (siblingRace == "斑猫人")
            return Random.Array(names.斑猫人.Name);
        else
            name = (siblingRace == "人类" && character.Race.name != "人类") ?
                Names.GetHuman(Names.GetHumanEthnicity(), sibling.Gender) :
                Names.Get(sibling.Race, sibling.Gender);
        let lastSpace = name.lastIndexOf(" ");
        return lastSpace < 0 ? name : name.substring(0, lastSpace);
    },

    阵营: function () {
        let roll = Random.DiceRoll("3d6");
        return roll < 4 ? Random.Array(["混乱邪恶", "混乱中立"]) :
            roll < 6 ? "守序邪恶" :
                roll < 9 ? "中立邪恶" :
                    roll < 13 ? "绝对中立" :
                        roll < 16 ? "中立善良" :
                            roll < 17 ? "守序善良" :
                                roll < 18 ? "守序中立" :
                                    Random.Array(["混乱善良", "混乱中立"]);
    },

    ClassWeighted: function () {
        let rand = Random.Num(115);
        return rand < 7 ? "野蛮人" :
            rand < 14 ? "吟游诗人" :
                rand < 29 ? "牧师" :
                    rand < 36 ? "德鲁伊" :
                        rand < 52 ? "战士" :
                            rand < 58 ? "武僧" :
                                rand < 64 ? "圣武士" :
                                    rand < 70 ? "游侠" :
                                        rand < 84 ? "游荡者" :
                                            rand < 89 ? "术士" :
                                                rand < 94 ? "邪术师" :
                                                    rand < 100 ? "法师" :
                                                        rand < 105 ? (usedBooks.includes("EBR") ? "奇械师" : this.ClassWeighted()) :
                                                            rand < 110 ? (usedBooks.includes("Other") ? "血猎人" : this.ClassWeighted()) :
                                                                (usedBooks.includes("UA") ? "灵能师" : this.ClassWeighted());
    },

    Status: function () {
        let roll = Random.DiceRoll("3d6");
        return roll < 4 ? "“死亡（在导致死亡的原因表上掷骰）”" :
            roll < 6 ? ""缺失或未知"" :
                roll < 9 ? "“活着，但由于受伤、财务困难或关系问题而表现不佳”" :
                    roll < 13 ? ""活着且健康"" :
                        roll < 16 ? "" 生存且非常成功"" :
                            roll < 18 ? ""活着且臭名昭著"" :
                                ""活着并且出名了"";
    },

    RaisedBy: function () {
        let rand = Random.Num(100);
        return rand < 1 ? "Nobody" :
            rand < 2 ? ""机构，如精神病院"" :
                rand < 3 ? "Temple" :
                    rand < 5 ? "Orphanage" :
                        rand < 7 ? "Guardian" :
                            rand < 15 ? "“父亲或母亲的姑妈、叔叔或其他亲属：或者部落或氏族等大家庭成员”" :
                                rand < 25 ? "“父系或母系祖父母”" :
                                    rand < 35 ? ""收养家庭（同种族或不同种族）"" :
                                        rand < 55 ? ""单身父亲或继父"" :
                                            rand < 75 ? ""单身母亲或继母"" :
                                                "母亲和父亲";
    },

    AbsentParent: function () {
        let rand = Random.Num(4);
        return rand < 1 ? ""你的父母死了"" :
            rand < 2 ? ""你的父母被监禁、奴役或以其他方式带走"" :
                rand < 3 ? ""你的父母抛弃了你"" :
                    ""你的父母失踪了，下落不明"";
    },

    Lifestyle: function () {
        let roll = Random.DiceRoll("3d6");
        return roll < 4 ? ["悲惨", -40] :
            roll < 6 ? ["肮脏", -20] :
                roll < 9 ? ["贫穷", -10] :
                    roll < 13 ? ["简朴", 0] :
                        roll < 16 ? ["舒适", 10] :
                            roll < 18 ? ["富裕", 20] : ["贵族", 40];
    },

    Home: function (lifeMod) {
        let rand = Random.Num(100) + lifeMod;
        return rand < 0 ? ""街头流浪"" :
            rand < 20 ? ""破旧的小屋"" :
                rand < 30 ? ""没有固定居所，你经常搬家"" :
                    rand < 40 ? "“野外村庄的营地”" :
                        rand < 50 ? "“破败街区中的公寓”" :
                            rand < 70 ? "小型 house" :
                                rand < 90 ? "大型 house" :
                                    rand < 110 ? "Mansion" :
                                        "“宫殿或城堡”";
    },

    Memories: function () {
        let roll = Random.DiceRoll("3d6") + Random.Num(5) - 1;
        return roll < 4 ? ""我仍然受到童年时期的困扰，那时我被同龄人欺负得很惨"" :
            roll < 6 ? ""我大部分童年都是独自一人，没有亲密的朋友"" :
                roll < 9 ? ""别人认为我与众不同或奇怪，所以我很少有同伴"" :
                    roll < 13 ? ""我有几个好朋友，并且度过了平凡的童年。"" :
                        roll < 16 ? ""我有几个朋友，我的童年总体上是快乐的。"" :
                            roll < 18 ? ""我总是觉得交朋友很容易，我喜欢和人在一起。"" :
                                "“每个人都知道我是谁，我在哪里都有朋友。”";
    },

    Relationship: function () {
        let roll = Random.DiceRoll("3d4");
        return roll < 5 ? "敌对" :
            roll < 11 ? "友善" :
                "漠不关心";
    },
}

var LockFunctions = {
    TryLock: function (id) {
        let button = $("#" + id + "-lock-button").children(":first"),
            lockThis = !lock[id];
        lock[id] = lockThis;
        button.prop("class", lockThis ? "fa fa-lock" : "fa fa-lock-open");
    },
    TryLockAll: function (id) {
        lock.all.forEach(function (id) {
            lock[id] = true;
            $("#" + id + "-lock-button").children(":first").prop("class", "fa fa-lock");
        });
    },
    TryUnlockAll: function (id) {
        lock.all.forEach(function (id) {
            lock[id] = false;
            $("#" + id + "-lock-button").children(":first").prop("class", "fa fa-lock-open");
        });
    }
}

// When the page loads
$(function () {
    let calls = 9, generateNew = false;
    const GetJSON = function (name) {
        $.getJSON("js/JSON/" + name + ".json", function (data) {
            window[name] = data;
            calls--;
            if (calls <= 0) {
                CharacterType.GetNoCard();
                拖放downs.Update();
                if (generateNew)
                    Generate.All();
                else {
                    Characters.LoadCharacter(character);
                    Characters.SaveCharacter();
                }
            }
        });
    }

    let savedData = localStorage.getItem("SavedCharacterData");
    if (savedData == undefined)
        generateNew = true;
    else
        character = JSON.parse(savedData);

    GetJSON("backgrounds");
    GetJSON("books");
    GetJSON("cardsources");
    GetJSON("classes");
    GetJSON("life");
    GetJSON("names");
    GetJSON("npcs");
    GetJSON("other");
    GetJSON("races");

    defaultRaceSectionClass = $("#race-section").prop("class");

    InitCardScript();
});

let Characters = {
    SaveCharacter: function () {
        prevCharacters.unshift(Object.assign({}, character));
        if (prevCharacters.length > 25)
            prevCharacters.pop();
        this.Set拖放down();
    },
    SaveToStorage: function () {
        localStorage.setItem("SavedCharacterData", JSON.stringify(character));
    },
    LoadCharacter: function (loadedCharacter) {
        character = Object.assign({}, loadedCharacter);
        Content.Get();
        CardType.Set();
        SetHTML();
        this.SaveToStorage();
    },
    Set拖放down: function () {
        if (prevCharacters.length < 2) return;
        let options = ["<option value=''>-选择-</option>"];
        for (let index = 0; index < prevCharacters.length; index++) {
            let prevCharacter = prevCharacters[index];
            options.push("<option value='" + index + "'>" + prevCharacter.ShortName + ", " + prevCharacter.Race.name + " " + (prevCharacter.type == "npc" ? prevCharacter.Occupation : prevCharacter.Class.name) + "</option>");
        }
        $("#recent-characters-拖放down").html(options.join(""));
        $("#recent-characters").show();
    },
    LoadFrom拖放down: function () {
        let num = $("#recent-characters-拖放down").val();
        if (num != "")
            this.LoadCharacter(prevCharacters[num]);
    }
}