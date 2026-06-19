tetrasList = {
    "外表": [],
    "aspect": [],
    "quirk": [],
    "适用对象": [],
    "utility": []
};
tetrasData = [], bookData = [], items = [];

function RandomNumber(max) {
    return Math.floor(Math.random() * max)
}

function RandomFromArray(arr) {
    return arr[RandomNumber(arr.length)];
}

function MakeList(arr) {
    let newArr = [];
    for (let index = 0; index < arr.length; index++) {
        let entry = arr[index];
        for (let repeat = 0; repeat < entry.weight; repeat++)
            newArr.push(entry.name);
    }
    return newArr;
}

$(function () {
    $.getJSON("JSON/tetras-data.json", function (tetrasJson) {
        tetrasData = tetrasJson;
        tetrasList.外表 = MakeList(tetrasData.外表);
        tetrasList.aspect = MakeList(tetrasData.aspect);
        tetrasList.quirk = MakeList(tetrasData.quirk);
        tetrasList.usedBy = MakeList(tetrasData.usedBy);
        tetrasList.utility = MakeList(tetrasData.utility);
    });
    $.getJSON("JSON/book-data.json", function (bookJson) {
        bookData = bookJson;
    });
    
    OnCheck();
});

function GetBooks(arr) {
    let books = [];
    arr.forEach(book => {
        switch (book) {
            case "发现":
                if ($("#探索-book").prop("checked"))
                    books.push("发现");
                break;
            case "描述/微型":
                if ($("#des微型-book").prop("checked"))
                    books.push("描述/微型");
                break;
            case ""构建明天"":
                if ($("#building-tomorrow-book").prop("checked"))
                    books.push(""构建明天"");
                break;
        }
    });
    return books;
}

function GenerateTetras() {
    let htmlItem =
        `<div><b>Aspect:</b> ${RandomFromArray(tetrasList.aspect)}</div>
        <div><b>Utility:</b> ${RandomFromArray(tetrasList.utility)}</div>
        <div><b>外表:</b> ${RandomFromArray(tetrasList.外表)}</div>
        <div><b>Used by:</b> ${RandomFromArray(tetrasList.usedBy)}</div>
        <div><b>怪癖:</b> ${RandomFromArray(tetrasList.quirk)}</div>`
    AddItem(htmlItem);
}

function GenerateCypherArtifact(type, is计划 = false) {
    let books = GetBooks(["发现", "发现", "描述/微型", ""构建明天""]),
        book = RandomFromArray(books),
        item = RandomFromArray(bookData[type][book]),
        htmlItem =
            `<div><b>${item.name}${is计划 ? "（计划）" : ""}</b></div>`
            + (item.levelDie > 0 ?
                (`<div>Level ${RandomNumber(item.levelDie) + item.levelBonus + 1} ${type} (` +
                    (item.levelBonus > 0 ?
                        `d${item.levelDie} + ${item.levelBonus})</div>` :
                        `d${item.levelDie})`)) :
                `<div>等级 ${item.levelBonus} ${type} (${item.levelBonus})</div>`)
            + `<div>最低制作等级：${item.minimumCraftingLevel}</div>`;
    AddItem(htmlItem);
}

function GenerateOddity() {
    let htmlItem = `<div><b>${RandomFromArray(bookData["Oddity"]["探索"])}</b></div><div>奇物</div>`em(htmlItem);
}

function GenerateOther(type, is计划 = false) {
    let book = (type == "生物" || type == "异空间") ? ""构建明天"" : 
        RandomFromArray(GetBooks(["描述/微型", ""构建明天""]));
        item = RandomFromArray(bookData[type][book]),
        htmlItem =
            `<div><b>${item.name}${is计划 ? " (设计图)" : ""}</b></div>`  AddItem(htmlItem);
}

function Generate计划() {
    let books = GetBooks(["发现", "发现", "描述/微型", ""构建明天""]),
        randomArr = [];
    if(books.includes("发现"))
        randomArr.push("密码", "密码", "密码", "神器", "神器")
    if(books.includes("描述/微型") || books.includes(""构建明天""))
        randomArr.push("密码", "密码", "密码", "神器", "神器",
            "设施", "设施", "设施", "设施", "设施",
            "构装体", "构装体", "构装体", "载具", "载具");
    if(books.includes(""构建明天""))
        randomArr.push("生物", "生物", "异空间", "异空间")
    
    let type = RandomFromArray(randomArr);
    if (type == "密码" || type == "神器")
        GenerateCypherArtifact(type, true);
    else
        GenerateOther(type, true);
}

function AddItem(htmlItem) {
    items.unshift(htmlItem)
    if (items.length > 5)
        items.pop();
    $("#items-list").html(items.join("<hr>"));
}

function OnCheck() {
    if ($("input:checkbox:checked").length > 0) {
        $("#generate-cypher, #generate-artifact, #generate-计划").prop("disabled", false)
        $("#generate-oddity").prop("disabled",
            !$("#探索-book").prop("checked"));
        $("#generate-installation, #generate-automaton, #generate-vehicle").prop("disabled", 
            !($("#des微型-book").prop("checked") || $("#building-tomorrow-book").prop("checked")));
        $("#generate-biological, #generate-otherspace").prop("disabled",
            !$("#building-tomorrow-book").prop("checked"));
    }
    else {
        $("button").prop("disabled", true)
        $("#generate-tetras").prop("disabled", false)
    }
}