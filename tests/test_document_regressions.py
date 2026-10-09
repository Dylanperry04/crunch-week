import io
import zipfile

import pytest

from crunch_week.documents import DocumentError, read_document


def archive_bytes(files):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    return output.getvalue()


def workbook(value="39267", date1904="1", format_id="14", extra_sheets=0):
    ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    files = {
        "xl/workbook.xml": f'<workbook xmlns="{ns}"><workbookPr date1904="{date1904}"/></workbook>',
        "xl/styles.xml": f'<styleSheet xmlns="{ns}"><cellXfs><xf numFmtId="{format_id}"/></cellXfs></styleSheet>',
        "xl/worksheets/sheet1.xml": (
            f'<worksheet xmlns="{ns}"><sheetData><row><c s="0"><v>{value}</v></c></row></sheetData></worksheet>'
        ),
    }
    for n in range(2, extra_sheets + 2):
        files[f"xl/worksheets/sheet{n}.xml"] = files["xl/worksheets/sheet1.xml"]
    return archive_bytes(files)


def test_zip_does_not_silently_drop_broken_supported_files():
    data = archive_bytes({"good.txt": "Essay due 2026-11-03", "broken.docx": b"not a document"})
    with pytest.raises(DocumentError, match="broken.docx"):
        read_document("handbooks.zip", data)


@pytest.mark.parametrize("date1904,value", [("1", "39267"), ("0", "40729")])
def test_excel_date_systems_produce_the_same_deadline(date1904, value):
    assert read_document("dates.xlsx", workbook(value, date1904)).pages == ("2011-07-05",)


def test_excel_time_is_not_invented_as_an_1899_date():
    assert read_document("times.xlsx", workbook("0.75", "0", "20")).pages == ("18:00",)


def test_excel_extra_sheets_are_rejected_instead_of_truncated():
    with pytest.raises(DocumentError, match="50"):
        read_document("many.xlsx", workbook(extra_sheets=50))


def test_bad_office_numeric_metadata_is_a_document_error():
    with pytest.raises(DocumentError):
        read_document("broken.xlsx", workbook(format_id="bad"))


def test_powerpoint_blank_slides_keep_source_numbering():
    ns = "http://schemas.openxmlformats.org/drawingml/2006/main"
    data = archive_bytes(
        {
            "ppt/slides/slide1.xml": f'<a:root xmlns:a="{ns}"/>',
            "ppt/slides/slide2.xml": f'<a:root xmlns:a="{ns}"><a:p><a:r><a:t>Exam 40%</a:t></a:r></a:p></a:root>',
        }
    )
    document = read_document("slides.pptx", data)
    assert document.pages == ("", "Exam 40%")
    assert "[PAGE 2]\nExam 40%" in document.text


def test_office_documents_have_a_worker_timeout(monkeypatch):
    monkeypatch.setattr("crunch_week.documents.PARSER_TIMEOUT", 0.001)
    with pytest.raises(DocumentError, match="timed out"):
        read_document("large.xlsx", workbook())


def test_powerpoint_follows_display_order_after_slides_are_rearranged():
    p = "http://schemas.openxmlformats.org/presentationml/2006/main"
    r = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    a = "http://schemas.openxmlformats.org/drawingml/2006/main"
    data = archive_bytes(
        {
            "ppt/presentation.xml": f'<p:presentation xmlns:p="{p}" xmlns:r="{r}"><p:sldIdLst>'
            '<p:sldId r:id="second"/><p:sldId r:id="first"/></p:sldIdLst></p:presentation>',
            "ppt/_rels/presentation.xml.rels": "<Relationships>"
            f'<Relationship Id="first" Type="{r}/slide" Target="slides/slide1.xml"/>'
            f'<Relationship Id="second" Type="{r}/slide" Target="/ppt/slides/slide2.xml"/></Relationships>',
            "ppt/slides/slide1.xml": f'<a:root xmlns:a="{a}"><a:p><a:r><a:t>Last</a:t></a:r></a:p></a:root>',
            "ppt/slides/slide2.xml": f'<a:root xmlns:a="{a}"><a:p><a:r><a:t>First</a:t></a:r></a:p></a:root>',
        }
    )
    assert read_document("rearranged.pptx", data).pages == ("First", "Last")
