const bindList = [];

function bind(elem) {
    bindList.forEach(b => {
        b(elem);
    })
}

function addQueryParam(url, key, value) {
    return url + ((url.indexOf('?') == -1) ? "?" : "&") + key + "=" + value;
}
