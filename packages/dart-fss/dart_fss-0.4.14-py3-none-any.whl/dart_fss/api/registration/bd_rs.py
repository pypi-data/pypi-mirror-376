# -*- coding: utf-8 -*-
from typing import Dict
from ..helper import api_request


def bd_rs(
    corp_code: str,
    bgn_de: str,
    end_de: str,
    api_key: str = None
) -> Dict:
    """ 증권신고서(채무증권) 내에 요약 정보를 제공합니다.

    Parameters
    ----------
    corp_code: str
        공시대상회사의 고유번호(8자리)※ 개발가이드 > 공시정보 > 고유번호 참고
    bgn_de: str
        검색시작 접수일자(YYYYMMDD) ※ 2015년 이후 부터 정보제공
    end_de: str
        검색종료 접수일자(YYYYMMDD) ※ 2015년 이후 부터 정보제공
    api_key: str, optional
        DART_API_KEY, 만약 환경설정 DART_API_KEY를 설정한 경우 제공하지 않아도 됨
    Returns
    -------
    dict
        채무증권
    """

    path = '/api/bdRs.json'

    return api_request(
        api_key=api_key,
        path=path,
        corp_code=corp_code,
        bgn_de=bgn_de,
        end_de=end_de,
    )
