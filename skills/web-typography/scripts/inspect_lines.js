/* inspect_lines.js: measure how text actually broke in a rendered page.

   Use in a browser (DevTools console, an agent's JavaScript tool, or Playwright):
     1. Evaluate this whole file in the page. It defines window.typoInspect.
     2. Call typoInspect(), or typoInspect({ selector: 'article p', runtRatio: 0.25, minLines: 2 }).
   Playwright:
     await page.addScriptTag({ path: 'scripts/inspect_lines.js' });
     const report = await page.evaluate(() => typoInspect());
   Repeat at several viewport widths (320, 375, 768, 1024, 1440): breaks depend on width.

   Returns a JSON-serialisable object:
     viewport           { width, height } in CSS px
     checked            number of text blocks measured
     measure            characters per line for running text (p, li, dd, blockquote, figcaption):
                        { median, p10, p90, lines }; the last line of each block is excluded
     findings           [{ type, selector, lines, detail, lastLine }]

   Finding types:
     runt-single-word   the last line holds one word
     runt-fragment      the last line holds only the end of a word broken across lines
                        (automatic hyphenation, or a break at a hyphen such as "2019-|2021")
     runt-short         the last line of running text is shorter than runtRatio of the text width
     column-stray       a block leaves fewer than minLines lines at the bottom of one column
                        (orphan, Schusterjunge) or at the top of the next (widow, Hurenkind)
     overflow           lines of a block extend past the viewport (an unbreakable word or group)
     page-overflow      the whole page scrolls horizontally
     measure-long / measure-short
                        median characters per line outside 45-75 for running text

   The numbers are measurements, not verdicts: judge them against the reading mode.
   Characters per line are counted from words on the line plus one space between words. */
(function () {
  'use strict';

  var RUNNING = 'p, li, dd, blockquote, figcaption';
  var DEFAULT_SELECTOR = 'p, li, dd, blockquote, figcaption, h1, h2, h3, h4, h5, h6';
  var NESTED_BLOCKS = 'p, li, h1, h2, h3, h4, h5, h6, blockquote, ul, ol, dl, div, figure, table';

  function cssPath(el) {
    var parts = [];
    while (el && el.nodeType === 1 && parts.length < 4) {
      var part = el.localName;
      if (el.id) { parts.unshift(part + '#' + el.id); break; }
      if (el.classList.length) part += '.' + Array.prototype.slice.call(el.classList, 0, 2).join('.');
      var parent = el.parentElement;
      if (parent) {
        var same = Array.prototype.filter.call(parent.children, function (c) { return c.localName === el.localName; });
        if (same.length > 1) part += ':nth-of-type(' + (same.indexOf(el) + 1) + ')';
      }
      parts.unshift(part);
      el = parent;
    }
    return parts.join(' > ');
  }

  // Group the element's words into visual lines, in reading order.
  function measureLines(el, wordSink) {
    var walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, {
      acceptNode: function (n) {
        return n.parentElement && n.parentElement.closest('script, style, svg, [hidden]')
          ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT;
      }
    });
    var lines = [];
    var current = null;
    var node;
    while ((node = walker.nextNode())) {
      var re = /\S+/g;
      var m;
      while ((m = re.exec(node.data))) {
        var range = document.createRange();
        range.setStart(node, m.index);
        range.setEnd(node, m.index + m[0].length);
        var rects = Array.prototype.filter.call(range.getClientRects(), function (r) { return r.width > 0 && r.height > 0; });
        if (!rects.length) continue;
        var total = rects.reduce(function (s, r) { return s + r.width; }, 0);
        if (wordSink && rects.length === 1) wordSink.push({ word: m[0], width: Math.round(rects[0].width) });
        for (var i = 0; i < rects.length; i++) {
          var r = rects[i];
          var mid = (r.top + r.bottom) / 2;
          var sameLine = current &&
            Math.abs(mid - (current.top + current.bottom) / 2) < Math.min(r.height, current.bottom - current.top) / 2 &&
            r.left >= current.right - 2;
          if (!sameLine) {
            current = { top: r.top, bottom: r.bottom, left: r.left, right: r.right, words: [], chars: 0, fragmentStart: i > 0 };
            lines.push(current);
          }
          current.top = Math.min(current.top, r.top);
          current.bottom = Math.max(current.bottom, r.bottom);
          current.left = Math.min(current.left, r.left);
          current.right = Math.max(current.right, r.right);
          var share = rects.length > 1 ? Math.max(1, Math.round(m[0].length * r.width / total)) : m[0].length;
          var piece = rects.length === 1 ? m[0] : (i === 0 ? m[0].slice(0, share) + '-' : m[0].slice(-share));
          current.chars += share + (current.words.length ? 1 : 0);
          current.words.push(piece);
        }
      }
    }
    return lines;
  }

  // A new fragment (column or page region) starts when a line sits higher than the one before.
  function fragments(lines) {
    var out = [];
    var cur = [];
    lines.forEach(function (l) {
      var prev = cur[cur.length - 1];
      if (prev && l.top < prev.top - 1) { out.push(cur); cur = []; }
      cur.push(l);
    });
    if (cur.length) out.push(cur);
    return out;
  }

  function percentile(sorted, p) {
    if (!sorted.length) return null;
    var idx = Math.min(sorted.length - 1, Math.max(0, Math.round(p * (sorted.length - 1))));
    return sorted[idx];
  }

  window.typoInspect = function (options) {
    var o = Object.assign({ selector: DEFAULT_SELECTOR, runtRatio: 0.25, minLines: 2, maxFindings: 200 }, options || {});
    var findings = [];
    var cpl = [];
    var words = [];
    var checked = 0;

    Array.prototype.forEach.call(document.querySelectorAll(o.selector), function (el) {
      if (el.querySelector(NESTED_BLOCKS)) return;          // measure the innermost blocks only
      var boxes = el.getClientRects();
      if (!boxes.length) return;                            // not rendered
      var lines = measureLines(el, words);
      if (!lines.length) return;
      checked++;

      var cs = getComputedStyle(el);
      var width = boxes[0].width - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
      var running = el.matches(RUNNING);
      var selector = cssPath(el);
      var last = lines[lines.length - 1];
      var lastLine = last.words.join(' ');

      if (running && lines.length >= 2) {
        lines.slice(0, -1).forEach(function (l) { cpl.push(l.chars); });
      }
      if (lines.length >= 2) {
        if (last.words.length === 1 && last.fragmentStart) {
          findings.push({ type: 'runt-fragment', selector: selector, lines: lines.length, detail: 'last line is only the end of a word broken across lines (hyphenation, or a break at a hyphen or dash)', lastLine: lastLine });
        } else if (last.words.length === 1) {
          findings.push({ type: 'runt-single-word', selector: selector, lines: lines.length, detail: 'one word alone on the last line', lastLine: lastLine });
        } else if (running && width > 0 && (last.right - last.left) / width < o.runtRatio) {
          findings.push({ type: 'runt-short', selector: selector, lines: lines.length,
            detail: 'last line fills ' + Math.round(100 * (last.right - last.left) / width) + '% of the text width', lastLine: lastLine });
        }
      }

      if (el.scrollWidth > el.clientWidth + 1 && cs.overflowX === 'visible') {
        var boxRight = boxes[0].right - parseFloat(cs.paddingRight);
        var over = lines.filter(function (l) { return l.right > boxRight + 1; });
        findings.push({ type: 'overflow', selector: selector, lines: lines.length,
          detail: 'text is wider than its box (' + el.scrollWidth + ' > ' + el.clientWidth + ' px): a word or no-break group cannot break',
          lastLine: over.length ? over[0].words.join(' ') : '' });
      }

      var frags = fragments(lines);
      if (frags.length > 1) {
        if (frags[0].length < o.minLines) {
          findings.push({ type: 'column-stray', selector: selector, lines: lines.length,
            detail: 'orphan (Schusterjunge): ' + frags[0].length + ' line(s) at the bottom of a column, the rest continues in the next',
            lastLine: frags[0][frags[0].length - 1].words.join(' ') });
        }
        var end = frags[frags.length - 1];
        if (end.length < o.minLines) {
          findings.push({ type: 'column-stray', selector: selector, lines: lines.length,
            detail: 'widow (Hurenkind): ' + end.length + ' line(s) at the top of the next column', lastLine: end[0].words.join(' ') });
        }
      }
    });

    cpl.sort(function (a, b) { return a - b; });
    var median = percentile(cpl, 0.5);
    if (median !== null && cpl.length >= 5) {
      if (median > 75) findings.push({ type: 'measure-long', selector: o.selector, lines: cpl.length, detail: 'median ' + median + ' characters per line (target 45-75)' });
      if (median < 45) findings.push({ type: 'measure-short', selector: o.selector, lines: cpl.length, detail: 'median ' + median + ' characters per line (target 45-75; 40-50 is fine in columns)' });
    }

    var doc = document.documentElement;
    if (doc.scrollWidth > doc.clientWidth + 1) {
      words.sort(function (a, b) { return b.width - a.width; });
      var widest = words.slice(0, 3).map(function (w) { return w.word + ' (' + w.width + ' px)'; }).join(', ');
      findings.unshift({ type: 'page-overflow', selector: 'html', lines: 0,
        detail: 'the page is ' + doc.scrollWidth + ' px wide in a ' + doc.clientWidth + ' px viewport: horizontal scrolling (WCAG 1.4.10 at 320 px). ' +
          'Widest unbreakable words: ' + widest + '. A grid or flex track grows to fit its longest word, so one compound can widen a whole column.' });
    }

    return {
      viewport: { width: window.innerWidth, height: window.innerHeight },
      checked: checked,
      measure: { median: median, p10: percentile(cpl, 0.1), p90: percentile(cpl, 0.9), lines: cpl.length },
      findings: findings.slice(0, o.maxFindings),
      truncated: findings.length > o.maxFindings
    };
  };
})();
