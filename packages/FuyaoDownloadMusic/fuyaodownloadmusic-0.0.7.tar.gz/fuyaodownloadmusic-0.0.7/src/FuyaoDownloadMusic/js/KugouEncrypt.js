var nUtil = {}
var oUtil = {}
var rUtil = {}

nUtil.wordsToBytes = function (t) {
    for (var n = [], r = 0; r < 32 * t.length; r += 8)
        n.push(t[r >>> 5] >>> 24 - r % 32 & 255);
    return n
}

oUtil.stringToBytes = function (t) {
    for (var n = [], r = 0; r < t.length; r++)
        n.push(255 & t.charCodeAt(r));
    return n
}

nUtil.bytesToWords = function (t) {
    for (var n = [], r = 0, e = 0; r < t.length; r++,
        e += 8)
        n[e >>> 5] |= t[r] << 24 - e % 32;
    return n
}

rUtil.stringToBytes = function (t) {
    return oUtil.stringToBytes(unescape(encodeURIComponent(t)))
}

rUtil.rotl = function (t, n) {
    return t << n | t >>> 32 - n
}

nUtil.endian = function (t) {
    if (t.constructor == Number)
        return 16711935 & rUtil.rotl(t, 8) | 4278255360 & rUtil.rotl(t, 24);
    for (var n = 0; n < t.length; n++)
        t[n] = nUtil.endian(t[n]);
    return t
}

nUtil.bytesToHex = function (t) {
    for (var n = [], r = 0; r < t.length; r++)
        n.push((t[r] >>> 4).toString(16)),
            n.push((15 & t[r]).toString(16));
    return n.join("")
}

function e(t) {
    return null != t && (o(t) || iUtil(t) || !!t._isBuffer)
}

var i = {}
i._ff = function (t, n, r, e, o, i, c) {
    var s = t + (n & r | ~n & e) + (o >>> 0) + c;
    return (s << i | s >>> 32 - i) + n
}

i._gg = function (t, n, r, e, o, i, c) {
    var s = t + (n & e | r & ~e) + (o >>> 0) + c;
    return (s << i | s >>> 32 - i) + n
}

i._hh = function (t, n, r, e, o, i, c) {
    var s = t + (n ^ r ^ e) + (o >>> 0) + c;
    return (s << i | s >>> 32 - i) + n
}

i._ii = function (t, n, r, e, o, i, c) {
    var s = t + (r ^ (n | ~e)) + (o >>> 0) + c;
    return (s << i | s >>> 32 - i) + n
}

i._blocksize = 16
i._digestsize = 16

var iUtil = function (t, c) {
    t.constructor == String ? t = c && "binary" === c.encoding ? oUtil.stringToBytes(t) : rUtil.stringToBytes(t) : e(t) ? t = Array.prototype.slice.call(t, 0) : Array.isArray(t) || (t = t.toString());
    for (var s = nUtil.bytesToWords(t), a = 8 * t.length, l = 1732584193, u = -271733879, f = -1732584194, d = 271733878, g = 0; g < s.length; g++)
        s[g] = 16711935 & (s[g] << 8 | s[g] >>> 24) | 4278255360 & (s[g] << 24 | s[g] >>> 8);
    s[a >>> 5] |= 128 << a % 32,
        s[14 + (a + 64 >>> 9 << 4)] = a;
    for (var b = i._ff, p = i._gg, h = i._hh, m = i._ii, g = 0; g < s.length; g += 16) {
        var y = l
            , j = u
            , S = f
            , v = d;
        u = m(u = m(u = m(u = m(u = h(u = h(u = h(u = h(u = p(u = p(u = p(u = p(u = b(u = b(u = b(u = b(u, f = b(f, d = b(d, l = b(l, u, f, d, s[g + 0], 7, -680876936), u, f, s[g + 1], 12, -389564586), l, u, s[g + 2], 17, 606105819), d, l, s[g + 3], 22, -1044525330), f = b(f, d = b(d, l = b(l, u, f, d, s[g + 4], 7, -176418897), u, f, s[g + 5], 12, 1200080426), l, u, s[g + 6], 17, -1473231341), d, l, s[g + 7], 22, -45705983), f = b(f, d = b(d, l = b(l, u, f, d, s[g + 8], 7, 1770035416), u, f, s[g + 9], 12, -1958414417), l, u, s[g + 10], 17, -42063), d, l, s[g + 11], 22, -1990404162), f = b(f, d = b(d, l = b(l, u, f, d, s[g + 12], 7, 1804603682), u, f, s[g + 13], 12, -40341101), l, u, s[g + 14], 17, -1502002290), d, l, s[g + 15], 22, 1236535329), f = p(f, d = p(d, l = p(l, u, f, d, s[g + 1], 5, -165796510), u, f, s[g + 6], 9, -1069501632), l, u, s[g + 11], 14, 643717713), d, l, s[g + 0], 20, -373897302), f = p(f, d = p(d, l = p(l, u, f, d, s[g + 5], 5, -701558691), u, f, s[g + 10], 9, 38016083), l, u, s[g + 15], 14, -660478335), d, l, s[g + 4], 20, -405537848), f = p(f, d = p(d, l = p(l, u, f, d, s[g + 9], 5, 568446438), u, f, s[g + 14], 9, -1019803690), l, u, s[g + 3], 14, -187363961), d, l, s[g + 8], 20, 1163531501), f = p(f, d = p(d, l = p(l, u, f, d, s[g + 13], 5, -1444681467), u, f, s[g + 2], 9, -51403784), l, u, s[g + 7], 14, 1735328473), d, l, s[g + 12], 20, -1926607734), f = h(f, d = h(d, l = h(l, u, f, d, s[g + 5], 4, -378558), u, f, s[g + 8], 11, -2022574463), l, u, s[g + 11], 16, 1839030562), d, l, s[g + 14], 23, -35309556), f = h(f, d = h(d, l = h(l, u, f, d, s[g + 1], 4, -1530992060), u, f, s[g + 4], 11, 1272893353), l, u, s[g + 7], 16, -155497632), d, l, s[g + 10], 23, -1094730640), f = h(f, d = h(d, l = h(l, u, f, d, s[g + 13], 4, 681279174), u, f, s[g + 0], 11, -358537222), l, u, s[g + 3], 16, -722521979), d, l, s[g + 6], 23, 76029189), f = h(f, d = h(d, l = h(l, u, f, d, s[g + 9], 4, -640364487), u, f, s[g + 12], 11, -421815835), l, u, s[g + 15], 16, 530742520), d, l, s[g + 2], 23, -995338651), f = m(f, d = m(d, l = m(l, u, f, d, s[g + 0], 6, -198630844), u, f, s[g + 7], 10, 1126891415), l, u, s[g + 14], 15, -1416354905), d, l, s[g + 5], 21, -57434055), f = m(f, d = m(d, l = m(l, u, f, d, s[g + 12], 6, 1700485571), u, f, s[g + 3], 10, -1894986606), l, u, s[g + 10], 15, -1051523), d, l, s[g + 1], 21, -2054922799), f = m(f, d = m(d, l = m(l, u, f, d, s[g + 8], 6, 1873313359), u, f, s[g + 15], 10, -30611744), l, u, s[g + 6], 15, -1560198380), d, l, s[g + 13], 21, 1309151649), f = m(f, d = m(d, l = m(l, u, f, d, s[g + 4], 6, -145523070), u, f, s[g + 11], 10, -1120210379), l, u, s[g + 2], 15, 718787259), d, l, s[g + 9], 21, -343485551),
            l = l + y >>> 0,
            u = u + j >>> 0,
            f = f + S >>> 0,
            d = d + v >>> 0
    }
    return nUtil.endian([l, u, f, d])
}


var encrypt = function (t, r) {
    var e = nUtil.wordsToBytes(iUtil(t, r));
    return r && r.asBytes ? e : r && r.asString ? o.bytesToString(e) : nUtil.bytesToHex(e)
}


var main = function (dataList) {
    // var s = new Array([
    //     "NVPh5oo715z5DIWAeQlhMDsWXXQV4hwt",
    //     "appid=1014",
    //     "bitrate=0",
    //     "callback=callback123",
    //     "clienttime=" + clientTime,
    //     "clientver=1000",
    //     "dfid=1bq3hS0l3VXG3BD65H3ey1iP",
    //     "filter=10",
    //     "inputtype=0",
    //     "iscorrection=1",
    //     "isfuzzy=0",
    //     "keyword=" + keyword,
    //     "mid=c225a1e5d5acd9c6d0ba1255f58ddaf5",
    //     "page=1",
    //     "pagesize=" + 30,
    //     "platform=WebFilter",
    //     "privilege_filter=0",
    //     "srcappid=2919",
    //     "token=",
    //     "userid=0",
    //     "uuid=c225a1e5d5acd9c6d0ba1255f58ddaf5",
    //     "NVPh5oo715z5DIWAeQlhMDsWXXQV4hwt"
    // ])
    //
    // s = s.join("").replaceAll(",", "")

    // console.log(s)

    console.log(dataList)

    var encrypted = encrypt(dataList, undefined)


    console.log(encrypted)

    return encrypted


}

main('NVPh5oo715z5DIWAeQlhMDsWXXQV4hwtappid=1014clienttime=1757579237clientver=1000dfid=1bq3hS0l3VXG3BD65H3ey1iPmid=c225a1e5d5acd9c6d0ba1255f58ddaf5srcappid=2919uuid=1757579236863{"userid":"2402675940","plat":103,"m_type":0,"vip_type":0,"own_ads":{}}NVPh5oo715z5DIWAeQlhMDsWXXQV4hwt')
