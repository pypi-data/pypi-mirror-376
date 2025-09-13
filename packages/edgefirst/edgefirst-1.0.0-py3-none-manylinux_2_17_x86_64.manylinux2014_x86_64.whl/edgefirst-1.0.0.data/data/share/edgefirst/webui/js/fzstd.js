var gr = ArrayBuffer
    , F = Uint8Array
    , _ = Uint16Array
    , zr = Int16Array
    , s = Int32Array
    , t = function (r, e, i) {
        if (F.prototype.slice)
            return F.prototype.slice.call(r, e, i);
        (e == null || e < 0) && (e = 0),
            (i == null || i > r.length) && (i = r.length);
        var n = new F(i - e);
        return n.set(r.subarray(e, i)),
            n
    }
    , N = function (r, e, i, n) {
        if (F.prototype.fill)
            return F.prototype.fill.call(r, e, i, n);
        for ((i == null || i < 0) && (i = 0),
            (n == null || n > r.length) && (n = r.length); i < n; ++i)
            r[i] = e;
        return r
    }
    , fr = function (r, e, i, n) {
        if (F.prototype.copyWithin)
            return F.prototype.copyWithin.call(r, e, i, n);
        for ((i == null || i < 0) && (i = 0),
            (n == null || n > r.length) && (n = r.length); i < n;)
            r[e++] = r[i++]
    }
    , pr = {
        InvalidData: 0,
        WindowSizeTooLarge: 1,
        InvalidBlockType: 2,
        FSEAccuracyTooHigh: 3,
        DistanceTooFarBack: 4,
        UnexpectedEOF: 5
    }
    , Er = ["invalid zstd data", "window size too large (>2046MB)", "invalid block type", "FSE accuracy too high", "match distance too far back", "unexpected EOF"]
    , z = function (r, e, i) {
        var n = new Error(e || Er[r]);
        if (n.code = r,
            Error.captureStackTrace && Error.captureStackTrace(n, z),
            !i)
            throw n;
        return n
    }
    , yr = function (r, e, i) {
        for (var n = 0, a = 0; n < i; ++n)
            a |= r[e++] << (n << 3);
        return a
    }
    , Ar = function (r, e) {
        return (r[e] | r[e + 1] << 8 | r[e + 2] << 16 | r[e + 3] << 24) >>> 0
    }
    , or = function (r, e) {
        var i = r[0] | r[1] << 8 | r[2] << 16;
        if (i == 3126568 && r[3] == 253) {
            var n = r[4]
                , a = n >> 5 & 1
                , h = n >> 2 & 1
                , v = n & 3
                , l = n >> 6;
            n & 8 && z(0);
            var w = 6 - a
                , p = v == 3 ? 4 : v
                , S = yr(r, w, p);
            w += p;
            var g = l ? 1 << l : a
                , E = yr(r, w, g) + (l == 1 && 256)
                , T = E;
            if (!a) {
                var x = 1 << 10 + (r[5] >> 3);
                T = x + (x >> 3) * (r[5] & 7)
            }
            T > 2145386496 && z(1);
            var o = new F((e == 1 ? E || T : e ? 0 : T) + 12);
            return o[0] = 1,
                o[4] = 4,
                o[8] = 8,
            {
                b: w + g,
                y: 0,
                l: 0,
                d: S,
                w: e && e != 1 ? e : o.subarray(12),
                e: T,
                o: new s(o.buffer, 0, 3),
                u: E,
                c: h,
                m: Math.min(131072, T)
            }
        } else if ((i >> 4 | r[3] << 20) == 25481893)
            return Ar(r, 4) + 8;
        z(0)
    }
    , Z = function (r) {
        for (var e = 0; 1 << e <= r; ++e)
            ;
        return e - 1
    }
    , P = function (r, e, i) {
        var n = (e << 3) + 4
            , a = (r[e] & 15) + 5;
        a > i && z(3);
        for (var h = 1 << a, v = h, l = -1, w = -1, p = -1, S = h, g = new gr(512 + (h << 2)), E = new zr(g, 0, 256), T = new _(g, 0, 256), x = new _(g, 512, h), o = 512 + (h << 1), A = new F(g, o, h), c = new F(g, o + h); l < 255 && v > 0;) {
            var m = Z(v + 1)
                , B = n >> 3
                , H = (1 << m + 1) - 1
                , D = (r[B] | r[B + 1] << 8 | r[B + 2] << 16) >> (n & 7) & H
                , f = (1 << m) - 1
                , I = H - v - 1
                , W = D & f;
            if (W < I ? (n += m,
                D = W) : (n += m + 1,
                    D > f && (D -= I)),
                E[++l] = --D,
                D == -1 ? (v += D,
                    A[--S] = l) : v -= D,
                !D)
                do {
                    var j = n >> 3;
                    w = (r[j] | r[j + 1] << 8) >> (n & 7) & 3,
                        n += 2,
                        l += w
                } while (w == 3)
        }
        (l > 255 || v) && z(0);
        for (var M = 0, q = (h >> 1) + (h >> 3) + 3, C = h - 1, O = 0; O <= l; ++O) {
            var u = E[O];
            if (u < 1) {
                T[O] = -u;
                continue
            }
            for (p = 0; p < u; ++p) {
                A[M] = O;
                do
                    M = M + q & C;
                while (M >= S)
            }
        }
        for (M && z(0),
            p = 0; p < h; ++p) {
            var y = T[A[p]]++
                , U = c[p] = a - Z(y);
            x[p] = (y << U) - h
        }
        return [n + 7 >> 3, {
            b: a,
            s: A,
            n: c,
            t: x
        }]
    }
    , Fr = function (r, e) {
        var i = 0
            , n = -1
            , a = new F(292)
            , h = r[e]
            , v = a.subarray(0, 256)
            , l = a.subarray(256, 268)
            , w = new _(a.buffer, 268);
        if (h < 128) {
            var p = P(r, e + 1, 6)
                , S = p[0]
                , g = p[1];
            e += h;
            var E = S << 3
                , T = r[e];
            T || z(0);
            for (var x = 0, o = 0, A = g.b, c = A, m = (++e << 3) - 8 + Z(T); !(m -= A,
                m < E);) {
                var B = m >> 3;
                if (x += (r[B] | r[B + 1] << 8) >> (m & 7) & (1 << A) - 1,
                    v[++n] = g.s[x],
                    m -= c,
                    m < E)
                    break;
                B = m >> 3,
                    o += (r[B] | r[B + 1] << 8) >> (m & 7) & (1 << c) - 1,
                    v[++n] = g.s[o],
                    A = g.n[x],
                    x = g.t[x],
                    c = g.n[o],
                    o = g.t[o]
            }
            ++n > 255 && z(0)
        } else {
            for (n = h - 127; i < n; i += 2) {
                var H = r[++e];
                v[i] = H >> 4,
                    v[i + 1] = H & 15
            }
            ++e
        }
        var D = 0;
        for (i = 0; i < n; ++i) {
            var f = v[i];
            f > 11 && z(0),
                D += f && 1 << f - 1
        }
        var I = Z(D) + 1
            , W = 1 << I
            , j = W - D;
        for (j & j - 1 && z(0),
            v[n++] = Z(j) + 1,
            i = 0; i < n; ++i) {
            var f = v[i];
            ++l[v[i] = f && I + 1 - f]
        }
        var M = new F(W << 1)
            , q = M.subarray(0, W)
            , C = M.subarray(W);
        for (w[I] = 0,
            i = I; i > 0; --i) {
            var O = w[i];
            N(C, i, O, w[i - 1] = O + l[i] * (1 << I - i))
        }
        for (w[0] != W && z(0),
            i = 0; i < n; ++i) {
            var u = v[i];
            if (u) {
                var y = w[u];
                N(q, i, y, w[u] = y + (1 << I - u))
            }
        }
        return [e, {
            n: C,
            b: I,
            s: q
        }]
    }
    , Tr = P(new F([81, 16, 99, 140, 49, 198, 24, 99, 12, 33, 196, 24, 99, 102, 102, 134, 70, 146, 4]), 0, 6)[1]
    , Br = P(new F([33, 20, 196, 24, 99, 140, 33, 132, 16, 66, 8, 33, 132, 16, 66, 8, 33, 68, 68, 68, 68, 68, 68, 68, 68, 36, 9]), 0, 6)[1]
    , Dr = P(new F([32, 132, 16, 66, 102, 70, 68, 68, 68, 68, 36, 73, 2]), 0, 5)[1]
    , lr = function (r, e) {
        for (var i = r.length, n = new s(i), a = 0; a < i; ++a)
            n[a] = e,
                e += 1 << r[a];
        return n
    }
    , d = new F(new s([0, 0, 0, 0, 16843009, 50528770, 134678020, 202050057, 269422093]).buffer, 0, 36)
    , Sr = lr(d, 0)
    , rr = new F(new s([0, 0, 0, 0, 0, 0, 0, 0, 16843009, 50528770, 117769220, 185207048, 252579084, 16]).buffer, 0, 53)
    , mr = lr(rr, 3)
    , Q = function (r, e, i) {
        var n = r.length
            , a = e.length
            , h = r[n - 1]
            , v = (1 << i.b) - 1
            , l = -i.b;
        h || z(0);
        for (var w = 0, p = i.b, S = (n << 3) - 8 + Z(h) - p, g = -1; S > l && g < a;) {
            var E = S >> 3
                , T = (r[E] | r[E + 1] << 8 | r[E + 2] << 16) >> (S & 7);
            w = (w << p | T) & v,
                e[++g] = i.s[w],
                S -= p = i.n[w]
        }
        (S != l || g + 1 != a) && z(0)
    }
    , xr = function (r, e, i) {
        var n = 6
            , a = e.length
            , h = a + 3 >> 2
            , v = h << 1
            , l = h + v;
        Q(r.subarray(n, n += r[0] | r[1] << 8), e.subarray(0, h), i),
            Q(r.subarray(n, n += r[2] | r[3] << 8), e.subarray(h, v), i),
            Q(r.subarray(n, n += r[4] | r[5] << 8), e.subarray(v, l), i),
            Q(r.subarray(n), e.subarray(l), i)
    }
    , wr = function (r, e, i) {
        var n, a = e.b, h = r[a], v = h >> 1 & 3;
        e.l = h & 1;
        var l = h >> 3 | r[a + 1] << 5 | r[a + 2] << 13
            , w = (a += 3) + l;
        if (v == 1)
            return a >= r.length ? void 0 : (e.b = a + 1,
                i ? (N(i, r[a], e.y, e.y += l),
                    i) : N(new F(l), r[a]));
        if (w > r.length)
            return;
        if (v == 0)
            return e.b = w,
                i ? (i.set(r.subarray(a, w), e.y),
                    e.y += l,
                    i) : t(r, a, w);
        if (v == 2) {
            var p = r[a]
                , S = p & 3
                , g = p >> 2 & 3
                , E = p >> 4
                , T = 0
                , x = 0;
            S < 2 ? g & 1 ? E |= r[++a] << 4 | (g & 2 && r[++a] << 12) : E = p >> 3 : (x = g,
                g < 2 ? (E |= (r[++a] & 63) << 4,
                    T = r[a] >> 6 | r[++a] << 2) : g == 2 ? (E |= r[++a] << 4 | (r[++a] & 3) << 12,
                        T = r[a] >> 2 | r[++a] << 6) : (E |= r[++a] << 4 | (r[++a] & 63) << 12,
                            T = r[a] >> 6 | r[++a] << 2 | r[++a] << 10)),
                ++a;
            var o = i ? i.subarray(e.y, e.y + e.m) : new F(e.m)
                , A = o.length - E;
            if (S == 0)
                o.set(r.subarray(a, a += E), A);
            else if (S == 1)
                N(o, r[a++], A);
            else {
                var c = e.h;
                if (S == 2) {
                    var m = Fr(r, a);
                    T += a - (a = m[0]),
                        e.h = c = m[1]
                } else
                    c || z(0);
                (x ? xr : Q)(r.subarray(a, a += T), o.subarray(A), c)
            }
            var B = r[a++];
            if (B) {
                B == 255 ? B = (r[a++] | r[a++] << 8) + 32512 : B > 127 && (B = B - 128 << 8 | r[a++]);
                var H = r[a++];
                H & 3 && z(0);
                for (var D = [Br, Dr, Tr], f = 2; f > -1; --f) {
                    var I = H >> (f << 1) + 2 & 3;
                    if (I == 1) {
                        var W = new F([0, 0, r[a++]]);
                        D[f] = {
                            s: W.subarray(2, 3),
                            n: W.subarray(0, 1),
                            t: new _(W.buffer, 0, 1),
                            b: 0
                        }
                    } else
                        I == 2 ? (n = P(r, a, 9 - (f & 1)),
                            a = n[0],
                            D[f] = n[1]) : I == 3 && (e.t || z(0),
                                D[f] = e.t[f])
                }
                var j = e.t = D
                    , M = j[0]
                    , q = j[1]
                    , C = j[2]
                    , O = r[w - 1];
                O || z(0);
                var u = (w << 3) - 8 + Z(O) - C.b
                    , y = u >> 3
                    , U = 0
                    , R = (r[y] | r[y + 1] << 8) >> (u & 7) & (1 << C.b) - 1;
                y = (u -= q.b) >> 3;
                var V = (r[y] | r[y + 1] << 8) >> (u & 7) & (1 << q.b) - 1;
                y = (u -= M.b) >> 3;
                var X = (r[y] | r[y + 1] << 8) >> (u & 7) & (1 << M.b) - 1;
                for (++B; --B;) {
                    var k = C.s[R]
                        , ir = C.n[R]
                        , b = M.s[X]
                        , ar = M.n[X]
                        , nr = q.s[V]
                        , vr = q.n[V];
                    y = (u -= nr) >> 3;
                    var hr = 1 << nr
                        , L = hr + ((r[y] | r[y + 1] << 8 | r[y + 2] << 16 | r[y + 3] << 24) >>> (u & 7) & hr - 1);
                    y = (u -= rr[b]) >> 3;
                    var G = mr[b] + ((r[y] | r[y + 1] << 8 | r[y + 2] << 16) >> (u & 7) & (1 << rr[b]) - 1);
                    y = (u -= d[k]) >> 3;
                    var Y = Sr[k] + ((r[y] | r[y + 1] << 8 | r[y + 2] << 16) >> (u & 7) & (1 << d[k]) - 1);
                    if (y = (u -= ir) >> 3,
                        R = C.t[R] + ((r[y] | r[y + 1] << 8) >> (u & 7) & (1 << ir) - 1),
                        y = (u -= ar) >> 3,
                        X = M.t[X] + ((r[y] | r[y + 1] << 8) >> (u & 7) & (1 << ar) - 1),
                        y = (u -= vr) >> 3,
                        V = q.t[V] + ((r[y] | r[y + 1] << 8) >> (u & 7) & (1 << vr) - 1),
                        L > 3)
                        e.o[2] = e.o[1],
                            e.o[1] = e.o[0],
                            e.o[0] = L -= 3;
                    else {
                        var $ = L - (Y != 0);
                        $ ? (L = $ == 3 ? e.o[0] - 1 : e.o[$],
                            $ > 1 && (e.o[2] = e.o[1]),
                            e.o[1] = e.o[0],
                            e.o[0] = L) : L = e.o[0]
                    }
                    for (var f = 0; f < Y; ++f)
                        o[U + f] = o[A + f];
                    U += Y,
                        A += Y;
                    var J = U - L;
                    if (J < 0) {
                        var K = -J
                            , ur = e.e + J;
                        K > G && (K = G);
                        for (var f = 0; f < K; ++f)
                            o[U + f] = e.w[ur + f];
                        U += K,
                            G -= K,
                            J = 0
                    }
                    for (var f = 0; f < G; ++f)
                        o[U + f] = o[J + f];
                    U += G
                }
                if (U != A)
                    for (; A < o.length;)
                        o[U++] = o[A++];
                else
                    U = o.length;
                i ? e.y += U : o = t(o, 0, U)
            } else if (i) {
                if (e.y += E,
                    A)
                    for (var f = 0; f < E; ++f)
                        o[f] = o[A + f]
            } else
                A && (o = t(o, A));
            return e.b = w,
                o
        }
        z(2)
    }
    , er = function (r, e) {
        if (r.length == 1)
            return r[0];
        for (var i = new F(e), n = 0, a = 0; n < r.length; ++n) {
            var h = r[n];
            i.set(h, a),
                a += h.length
        }
        return i
    };
function Ir(r, e) {
    for (var i = [], n = +!e, a = 0, h = 0; r.length;) {
        var v = or(r, n || e);
        if (typeof v == "object") {
            for (n ? (e = null,
                v.w.length == v.u && (i.push(e = v.w),
                    h += v.u)) : (i.push(e),
                        v.e = 0); !v.l;) {
                var l = wr(r, v, e);
                l || z(5),
                    e ? v.e = v.y : (i.push(l),
                        h += l.length,
                        fr(v.w, 0, l.length),
                        v.w.set(l, v.w.length - l.length))
            }
            a = v.b + v.c * 4
        } else
            a = v;
        r = r.subarray(a)
    }
    return er(i, h)
}
var Mr = function () {
    function r(e) {
        this.ondata = e,
            this.c = [],
            this.l = 0,
            this.z = 0
    }
    return r.prototype.push = function (e, i) {
        if (typeof this.s == "number") {
            var n = Math.min(e.length, this.s);
            e = e.subarray(n),
                this.s -= n
        }
        var a = e.length
            , h = a + this.l;
        if (!this.s) {
            if (i) {
                if (!h) {
                    this.ondata(new F(0), !0);
                    return
                }
                h < 5 && z(5)
            } else if (h < 18) {
                this.c.push(e),
                    this.l = h;
                return
            }
            if (this.l && (this.c.push(e),
                e = er(this.c, h),
                this.c = [],
                this.l = 0),
                typeof (this.s = or(e)) == "number")
                return this.push(e, i)
        }
        if (typeof this.s != "number") {
            if (h < (this.z || 3)) {
                i && z(5),
                    this.c.push(e),
                    this.l = h;
                return
            }
            if (this.l && (this.c.push(e),
                e = er(this.c, h),
                this.c = [],
                this.l = 0),
                !this.z && h < (this.z = e[this.s.b] & 2 ? 4 : 3 + (e[this.s.b] >> 3 | e[this.s.b + 1] << 5 | e[this.s.b + 2] << 13))) {
                i && z(5),
                    this.c.push(e),
                    this.l = h;
                return
            } else
                this.z = 0;
            for (; ;) {
                var v = wr(e, this.s);
                if (v)
                    this.ondata(v, !1),
                        fr(this.s.w, 0, v.length),
                        this.s.w.set(v, this.s.w.length - v.length);
                else {
                    i && z(5);
                    var l = e.subarray(this.s.b);
                    this.s.b = 0,
                        this.c.push(l),
                        this.l += l.length;
                    return
                }
                if (this.s.l) {
                    var w = e.subarray(this.s.b);
                    this.s = this.s.c * 4,
                        this.push(w, i);
                    return
                }
            }
        } else
            i && z(5)
    }
        ,
        r
}();
export { Mr as Decompress, pr as ZstdErrorCode, Ir as decompress };
export default null;
