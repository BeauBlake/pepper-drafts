/**
 * Pepper draft site — feedback collector
 * =====================================================================
 * Receives Darren's review notes from the draft site and appends them to
 * a Google Sheet that Beau owns. No third party, no submission cap, and
 * nothing for Darren to sign up for.
 *
 * SETUP — about three minutes, once
 *  1. Go to sheets.new  → name it "Pepper site feedback".
 *  2. Extensions → Apps Script. Delete whatever is in the editor.
 *  3. Paste this whole file in. Save.
 *  4. Deploy → New deployment → gear icon → Web app.
 *       Execute as:        Me
 *       Who has access:    Anyone            ← must be "Anyone", not
 *                                              "Anyone with Google account",
 *                                              or Darren's browser gets a
 *                                              login page instead of a 200.
 *  5. Authorise when prompted (it is your own script writing to your own
 *     sheet; the "unverified app" warning is expected — Advanced →
 *     Go to project).
 *  6. Copy the /exec web app URL and send it to Beau.
 *
 * That URL goes into ENDPOINT at the top of review.js. Nothing else changes.
 *
 * NOTE ON CONTENT TYPE: the site posts as text/plain on purpose. An
 * application/json body would trigger a CORS preflight that Apps Script
 * does not answer, and the note would never arrive. Do not "fix" that.
 */

var SHEET_NAME = 'Notes';

function sheet_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(SHEET_NAME);
  if (!sh) {
    sh = ss.insertSheet(SHEET_NAME);
    sh.appendRow(['Received', 'Page', 'Type', 'Note',
                  'Original text', 'Suggested text', 'Where on page', 'URL']);
    sh.getRange('A1:H1').setFontWeight('bold');
    sh.setFrozenRows(1);
    sh.setColumnWidth(1, 150);
    sh.setColumnWidth(2, 140);
    sh.setColumnWidth(3, 70);
    sh.setColumnWidth(4, 380);
    sh.setColumnWidth(5, 300);
    sh.setColumnWidth(6, 300);
  }
  return sh;
}

function doPost(e) {
  try {
    var d = JSON.parse(e.postData.contents);
    sheet_().appendRow([
      new Date(),
      d.page || '',
      d.kind || 'pin',
      d.note || '',
      d.before || '',
      d.after || '',
      d.where || '',
      d.site || ''
    ]);
    return json_({ ok: true });
  } catch (err) {
    return json_({ ok: false, error: String(err) });
  }
}

/** Lets the feedback dashboard read every note back out. */
function doGet(e) {
  try {
    var sh = sheet_();
    var last = sh.getLastRow();
    if (last < 2) return json_({ ok: true, notes: [] });
    var rows = sh.getRange(2, 1, last - 1, 8).getValues();
    var out = rows.map(function (r) {
      return {
        at: r[0] ? new Date(r[0]).toISOString() : '',
        page: r[1], kind: r[2], note: r[3],
        before: r[4], after: r[5], where: r[6], site: r[7]
      };
    });
    return json_({ ok: true, notes: out });
  } catch (err) {
    return json_({ ok: false, error: String(err) });
  }
}

function json_(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
