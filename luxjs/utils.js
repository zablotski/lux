    var
    //
    ostring = Object.prototype.toString,
    //
    generateCallbacks = function () {
        var callbackFunctions = [],
            callFunctions = function () {
                var self = this,
                    args = slice.call(arguments, 0);
                callbackFunctions.forEach(function (f) {
                    f.apply(self, args);
                });
            };
        //
        callFunctions.add = function (f) {
            callbackFunctions.push(f);
        };
        return callFunctions;
    },
    //
    // Add a callback for an event to an element
    addEvent = lux.addEvent = function (element, event, callback) {
        var handler = element[event];
        if (!handler)
            element[event] = handler = generateCallbacks();
        if (handler.add)
            handler.add(callback);
    },
    //
    windowResize = lux.windowResize = function (callback) {
        addEvent(window, 'onresize', callback);
    },
    //
    windowHeight = lux.windowHeight = function () {
        return window.innerHeight > 0 ? window.innerHeight : screen.availHeight;
    },
    //
    isAbsolute = lux.isAbsolute = new RegExp('^([a-z]+://|//)'),
    //
    // Check if element has tagName tag
    isTag = function (element, tag) {
        element = $(element);
        return element.length === 1 && element[0].tagName === tag.toUpperCase();
    },
    //
    joinUrl = lux.joinUrl = function () {
        var bit, url = '';
        for (var i=0; i<arguments.length; ++i) {
            bit = arguments[i];
            if (bit) {
                var cbit = bit,
                    slash = false;
                // remove fron slashes if url has already some value
                while (url && cbit.substring(0, 1) === '/')
                    cbit = cbit.substring(1);
                // remove end slashes
                while (cbit.substring(cbit.length-1) === '/') {
                    slash = true;
                    cbit = cbit.substring(0, cbit.length-1);
                }
                if (cbit) {
                    if (url && url.substring(url.length-1) !== '/')
                        url += '/';
                    url += cbit;
                    if (slash)
                        url += '/';
                }
            }
        }
        return url;
    },
    //
    isObject = function (o) {
        return ostring.call(o) === '[object Object]';
    },
    //
    getRootAttribute = function (name) {
        var obj = root,
            bits= name.split('.');

        for (var i=0; i<bits.length; ++i) {
            obj = obj[bits[i]];
            if (!obj) break;
        }
        return obj;
    },
    //
    //  getOPtions
    //  ===============
    //
    //  Retrive options for the ``options`` string in ``attrs`` if available.
    //  Used by directive when needing to specify options in javascript rather
    //  than html data attributes.
    getOptions = lux.getOptions = function (attrs) {
        var options;
        if (attrs && typeof attrs.options === 'string') {
            options = getRootAttribute(attrs.options);
            if (typeof options === 'function')
                options = options();
        } else {
            options = {};
        }
        if (isObject(options))
            forEach(attrs, function (value, name) {
                if (name.substring(0, 1) !== '$' && name !== 'options')
                    options[name] = value;
            });
        return options;
    },
    //
    // random generated numbers for a uuid
    s4 = function () {
        return Math.floor((1 + Math.random()) * 0x10000)
                   .toString(16)
                   .substring(1);
    },
    //
    // Extend the initial array with values for other arrays
    extendArray = lux.extendArray = function () {
        if (!arguments.length) return;
        var value = arguments[0],
            push = function (v) {
                value.push(v);
            };
        if (typeof(value.push) === 'function') {
            for (var i=1; i<arguments.length; ++i)
                forEach(arguments[i], push);
        }
        return value;
    },
    //
    //  querySelector
    //  ===================
    //
    //  Simple wrapper for a querySelector
    querySelector = lux.querySelector = function (elem, query) {
        elem = $(elem);
        if (elem.length && query)
            return $(elem[0].querySelector(query));
        else
            return elem;
    },
    //
    //    LoadCss
    //  =======================
    //
    //  Load a style sheet link
    loadCss = lux.loadCss = function (filename) {
        var fileref = document.createElement("link");
        fileref.setAttribute("rel", "stylesheet");
        fileref.setAttribute("type", "text/css");
        fileref.setAttribute("href", filename);
        document.getElementsByTagName("head")[0].appendChild(fileref);
    },
    //
    //
    globalEval = lux.globalEval = function(data) {
        if (data) {
            // We use execScript on Internet Explorer
            // We use an anonymous function so that context is window
            // rather than jQuery in Firefox
            (root.execScript || function(data) {
                root["eval"].call(root, data );
            })(data);
        }
    },
    //
    // Simple Slugify function
    slugify = lux.slugify = function (str) {
        str = str.replace(/^\s+|\s+$/g, ''); // trim
        str = str.toLowerCase();

        // remove accents, swap ñ for n, etc
        var from = "àáäâèéëêìíïîòóöôùúüûñç·/_,:;";
        var to   = "aaaaeeeeiiiioooouuuunc------";
        for (var i=0, l=from.length ; i<l ; i++) {
            str = str.replace(new RegExp(from.charAt(i), 'g'), to.charAt(i));
        }

        str = str.replace(/[^a-z0-9 -]/g, '') // remove invalid chars
            .replace(/\s+/g, '-') // collapse whitespace and replace by -
            .replace(/-+/g, '-'); // collapse dashes

        return str;
    },
    //
    now = lux.now = function () {
        return Date.now ? Date.now() : new Date().getTime();
    },
    //
    size = lux.size = function (o) {
        if (!o) return 0;
        if (o.length !== undefined) return o.length;
        var n = 0;
        forEach(o, function () {
            ++n;
        });
        return n;
    };
