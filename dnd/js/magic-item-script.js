var dmgTables = {},
    homebrewTables = {},
    items = [];

const AddProp = (name, prop, buffer) => buffer.push("<b>" + name + ":</b> <i>" + prop.name + ".</i> " + prop.desc);

function GenerateDMG() {
    let subBuffer = [];

    subBuffer.push(GetItemType());
    AddProp("创造者", RandomFromArray(dmgTables.creator), subBuffer);
    AddProp("历史", RandomFromArray(dmgTables.history), subBuffer);

    let property = RandomFromArray(dmgTables.property);
    AddProp("特性", property, subBuffer);
    if (RandomNum(20) == 0)
        AddProp("特性", GetSecondProperty(dmgTables.property, property), subBuffer);

    AddProp("怪癖", RandomFromArray(dmgTables.quirk), subBuffer);
    AddToItemsList(subBuffer.join("<br>"));
}

function GenerateHomebrew() {
    let subBuffer = [];
    subBuffer.push(GetItemType());
    AddProp("出身", RandomFromArray(homebrewTables.origin), subBuffer);


    let majorprop = RandomFromArray(homebrewTables.majorprop);
    AddProp("主要特性", majorprop, subBuffer);
    if (RandomNum(15) == 0)
        AddProp("主要特性", GetSecondProperty(homebrewTables.majorprop, majorprop), subBuffer);

    let minorprop = RandomFromArray(homebrewTables.minorprop);
    AddProp("次要特性", RandomFromArray(homebrewTables.minorprop), subBuffer);
    if (RandomNum(15) == 0)
        AddProp("次要特性", GetSecondProperty(homebrewTables.minorprop, minorprop), subBuffer);

    let specialprop = RandomFromArray(homebrewTables.specialprop);
    AddProp("特殊特性", RandomFromArray(homebrewTables.specialprop), subBuffer);
    if (RandomNum(15) == 0)
        AddProp("特殊特性", GetSecondProperty(homebrewTables.specialprop, specialprop), subBuffer);

    AddToItemsList(subBuffer.join("<br>"));
}

function GetItemType() {
    let type = RandomFromArray(itemTypes);
    if (type == "护甲")
        return "<b>护甲 (" + RandomFromArray(armorTypes) + ")</b>";
    if (type == "武器")
        return "<b>武器 (" + RandomFromArray(weaponTypes) + ")</b>";
    if (type == "其他")
        return "<b>" + RandomFromArray(otherTypes) + "</b>";
    return "<b>奇物</b>";
}

function GetSecondProperty(table, firstprop) {
    let prop = null;
    do prop = table[RandomNum(table.length)];
    while (prop == firstprop);
    return prop;
}

function AddToItemsList(newItem) {
    items.unshift(newItem);
    if (items.length > 10)
        items.pop();
    $("#magic-items-list").html(items.join("<br><br>"));
}

function RandomNum(max) {
    return Math.floor(Math.random() * max);
}

function RandomFromArray(arr) {
    return arr[RandomNum(arr.length)];
}

// When the page loads
$(function () {
    $.getJSON("js/JSON/magic-item-specials.json", function (data) {
        dmgTables.creator = GetTable(data.creator);
        dmgTables.history = GetTable(data.history);
        dmgTables.property = GetTable(data.property);
        dmgTables.quirk = GetTable(data.quirk);
    });
    $.getJSON("js/JSON/magic-item-homebrews.json", function (data) {
        homebrewTables.origin = GetTable(data.origin);
        homebrewTables.majorprop = GetTable(data.majorprop);
        homebrewTables.minorprop = GetTable(data.minorprop);
        homebrewTables.specialprop = GetTable(data.specialprop);
    });
});

function GetTable(arr) {
    let newArr = []
    for (let index = 0; index < arr.length; index++) {
        let entry = arr[index];
        for (let repeat = 0; repeat < entry.weight; repeat++)
            newArr.push(entry);
    }
    return newArr;
}

const itemTypes = ["护甲", "武器", "武器", "奇物", "奇物", "其他"],
    armorTypes = ["镶钉皮甲", "胸甲", "半身板甲", "链甲", "板条甲", "全身板甲"],
    weaponTypes = ["匕首", "巨棒", "手斧", "标枪", "轻锤", "钉头锤", "木棍", "镰刀", "长矛", "轻弩", "短弓", "战斧", "连枷", "长柄刀", "巨斧", "巨剑", "长戟", "骑枪", "长剑", "重锤", "钉头锤", "长矛", "刺剑", "弯刀", "三叉戟", "战镐", "战锤", "长鞭", "手弩", "重弩", "长弓", "捕网"],
    otherTypes = ["乐器", "戒指", "权杖", "法杖", "魔杖"]