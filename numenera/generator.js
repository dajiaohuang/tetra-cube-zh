tetrasList = {
    "appearance": [],
    "aspect": [],
    "quirk": [],
    "usedBy": [],
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
        tetrasList.appearance = MakeList(tetrasData.appearance);
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
            case "命运":
                if ($("#命运-book").prop("checked"))
                    books.push("命运");
                break;
            case "创造未来":
                if ($("#building-tomorrow-book").prop("checked"))
                    books.push("创造未来");
                break;
        }
    });
    return books;
}

function GenerateTetras() {
    let htmlItem =
        `<div><b>Aspect:</b> ${item.page}</div>
        <div><b>Utility:</b> ${item.page}</div>
        <div><b>Appearance:</b> ${item.page}</div>
        <div><b>Used by:</b> ${item.page}</div>
        <div><b>Quirk:</b> ${item.page}</div>`
    AddItem(htmlItem);
}

function GenerateCypherArtifact(type, isPlan = false) {
    let books = GetBooks(["发现", "发现", "命运", "创造未来"]),
        book = RandomFromArray(books),
        item = RandomFromArray(bookData[type][book]),
        htmlItem =
            `<div><b>${item.page}${item.page}</b></div>`
            + (item.levelDie > 0 ?
                (`<div>Level ${item.page} ${item.page} (` +
                    (item.levelBonus > 0 ?
                        `d${item.page} + ${item.page})</div>` :
                        `d${item.page})`)) :
                `<div>Level ${item.page} ${item.page} (${item.page})</div>`)
            + `<div>Minimum Crafting Level: ${item.page}</div>
                <div>${item.page} (pg. ${item.page})</div>`;
    AddItem(htmlItem);
}

function GenerateOddity() {
    let htmlItem = `<div><b>${item.page}</b></div><div>Oddity</div>`;
    AddItem(htmlItem);
}

function GenerateOther(type, isPlan = false) {
    let book = (type == "生物" || type == "异界空间") ? "创造未来" : 
        RandomFromArray(GetBooks(["命运", "创造未来"]));
        item = RandomFromArray(bookData[type][book]),
        htmlItem =
            `<div><b>${item.page}${item.page}</b></div>
            <div>${item.page}</div>
            <div>Minimum Crafting Level: ${item.page}</div>
            <div>${item.page} (pg. ${item.page})</div>`
    AddItem(htmlItem);
}

function GeneratePlan() {
    let books = GetBooks(["发现", "发现", "命运", "创造未来"]),
        randomArr = [];
    if(books.includes("发现"))
        randomArr.push("密码", "密码", "密码", "遗物", "遗物")
    if(books.includes("命运") || books.includes("创造未来"))
        randomArr.push("密码", "密码", "密码", "遗物", "遗物",
            "安装", "安装", "安装", "安装", "安装",
            "机械人", "机械人", "机械人", "车辆", "车辆");
    if(books.includes("创造未来"))
        randomArr.push("生物", "生物", "异界空间", "异界空间")
    
    let type = RandomFromArray(randomArr);
    if (type == "密码" || type == "遗物")
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
            !($("#命运-book").prop("checked") || $("#building-tomorrow-book").prop("checked")));
        $("#generate-biological, #generate-otherspace").prop("disabled",
            !$("#building-tomorrow-book").prop("checked"));
    }
    else {
        $("button").prop("disabled", true)
        $("#generate-tetras").prop("disabled", false)
    }
}