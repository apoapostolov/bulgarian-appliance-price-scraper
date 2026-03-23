from technobulgarian_scraper import mcp_server as _legacy

main = _legacy.main
build_server = _legacy.build_server
parse_args = _legacy.parse_args
_latest_export_payloads = _legacy._latest_export_payloads
_latest_export_for_store_type = _legacy._latest_export_for_store_type
_latest_json_exports = _legacy._latest_json_exports
_match_score = _legacy._match_score


if __name__ == "__main__":
    raise SystemExit(main())
