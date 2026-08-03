/**
 * Progressive phone input: country dial code + national number formatting.
 * For +1 (NANP), formats as (XXX) XXX-XXXX while typing so mobile users
 * never need parentheses or dash keys.
 */
(function (global) {
  'use strict';

  function digitsOnly(value) {
    return String(value || '').replace(/\D/g, '');
  }

  function formatUsNational(digits) {
    var d = digitsOnly(digits).slice(0, 10);
    if (!d) return '';
    if (d.length <= 3) return '(' + d;
    if (d.length <= 6) return '(' + d.slice(0, 3) + ') ' + d.slice(3);
    return '(' + d.slice(0, 3) + ') ' + d.slice(3, 6) + '-' + d.slice(6);
  }

  function formatNational(digits, countryCode) {
    var code = digitsOnly(countryCode) || '1';
    var d = digitsOnly(digits);
    if (code === '1') return formatUsNational(d);
    d = d.slice(0, 15);
    var groups = [];
    for (var i = 0; i < d.length; i += 3) {
      groups.push(d.slice(i, i + 3));
    }
    return groups.join(' ');
  }

  function composePhone(countryCode, nationalDigits) {
    var code = digitsOnly(countryCode) || '1';
    var national = digitsOnly(nationalDigits);
    if (!national) return '';
    return ('+' + code + ' ' + formatNational(national, code)).trim();
  }

  function parseStoredPhone(value) {
    if (!value) return { countryCode: '1', nationalDigits: '' };
    var text = String(value).trim();
    var known = ['353', '91', '61', '52', '49', '44', '33', '1'];
    if (text.charAt(0) === '+') {
      var rest = text.slice(1);
      for (var i = 0; i < known.length; i++) {
        var code = known[i];
        if (rest.indexOf(code) === 0) {
          var national = digitsOnly(rest.slice(code.length));
          if (code === '1' && national.length === 11 && national.charAt(0) === '1') {
            national = national.slice(1);
          }
          return { countryCode: code, nationalDigits: national };
        }
      }
      var m = rest.match(/^(\d{1,3})\s*(.*)$/);
      if (m) {
        return { countryCode: m[1], nationalDigits: digitsOnly(m[2]) };
      }
    }
    var digits = digitsOnly(text);
    if (digits.length === 11 && digits.charAt(0) === '1') {
      return { countryCode: '1', nationalDigits: digits.slice(1) };
    }
    return { countryCode: '1', nationalDigits: digits };
  }

  function isValidPhone(value) {
    if (!value || !String(value).trim()) return false;
    var parsed = parseStoredPhone(value);
    if (parsed.countryCode === '1') return parsed.nationalDigits.length === 10;
    return parsed.nationalDigits.length >= 6 && parsed.nationalDigits.length <= 15;
  }

  function syncHidden(root) {
    var country = root.querySelector('.phone-country');
    var national = root.querySelector('.phone-national');
    var hidden = root.querySelector('.phone-full');
    if (!country || !national || !hidden) return;
    hidden.value = composePhone(country.value, national.value);
  }

  function bindPhoneInput(root) {
    if (!root || root.dataset.phoneBound === '1') return;
    root.dataset.phoneBound = '1';
    var country = root.querySelector('.phone-country');
    var national = root.querySelector('.phone-national');
    var hidden = root.querySelector('.phone-full');
    if (!country || !national || !hidden) return;

    var initial = hidden.value || root.getAttribute('data-initial') || '';
    var parsed = parseStoredPhone(initial);
    country.value = parsed.countryCode;
    if (![].some.call(country.options, function (o) { return o.value === country.value; })) {
      var opt = document.createElement('option');
      opt.value = parsed.countryCode;
      opt.textContent = '+' + parsed.countryCode;
      country.appendChild(opt);
      country.value = parsed.countryCode;
    }
    national.value = formatNational(parsed.nationalDigits, parsed.countryCode);
    syncHidden(root);

    national.addEventListener('input', function () {
      var caretAtEnd = national.selectionStart === national.value.length;
      var digits = digitsOnly(national.value);
      var maxLen = (digitsOnly(country.value) || '1') === '1' ? 10 : 15;
      digits = digits.slice(0, maxLen);
      national.value = formatNational(digits, country.value);
      if (caretAtEnd) {
        national.setSelectionRange(national.value.length, national.value.length);
      }
      syncHidden(root);
    });

    country.addEventListener('change', function () {
      var digits = digitsOnly(national.value);
      national.value = formatNational(digits, country.value);
      syncHidden(root);
    });

    var form = root.closest('form');
    if (form) {
      form.addEventListener('submit', function () {
        syncHidden(root);
      });
    }
  }

  function initAll(scope) {
    var root = scope || document;
    root.querySelectorAll('[data-phone-input]').forEach(bindPhoneInput);
  }

  global.PhoneInput = {
    digitsOnly: digitsOnly,
    formatUsNational: formatUsNational,
    formatNational: formatNational,
    composePhone: composePhone,
    parseStoredPhone: parseStoredPhone,
    isValidPhone: isValidPhone,
    initAll: initAll,
    bindPhoneInput: bindPhoneInput
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { initAll(); });
  } else {
    initAll();
  }
})(window);
