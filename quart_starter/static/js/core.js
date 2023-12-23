const bindList = [];

function bind(elem) {
    bindList.forEach(b => {
        b(elem);
    })
}
