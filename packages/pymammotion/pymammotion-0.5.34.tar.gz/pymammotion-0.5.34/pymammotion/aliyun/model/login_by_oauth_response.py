from dataclasses import dataclass

from mashumaro.mixins.orjson import DataClassORJSONMixin


@dataclass
class OpenAccount(DataClassORJSONMixin):
    displayName: str
    openId: str
    hasPassword: str
    subAccount: str
    pwdVersion: int
    mobileConflictAccount: str
    id: int
    mobileLocationCode: str
    avatarUrl: str
    domainId: int
    enableDevice: str
    status: int
    country: str | None = None


@dataclass
class OauthOtherInfo(DataClassORJSONMixin):
    SidExpiredTime: int


@dataclass
class LoginSuccessResult(DataClassORJSONMixin):
    reTokenExpireIn: int
    uidToken: str
    openAccount: OpenAccount
    initPwd: str
    sidExpireIn: int
    oauthOtherInfo: OauthOtherInfo
    refreshToken: str
    sid: str
    token: str


@dataclass
class InnerDataContent(DataClassORJSONMixin):
    loginSuccessResult: LoginSuccessResult
    mobileBindRequired: str


@dataclass
class InnerData(DataClassORJSONMixin):
    traceId: str
    vid: str
    code: int
    data: InnerDataContent
    subCode: int
    message: str
    successful: str
    deviceId: str | None = None


@dataclass
class LoginByOAuthResponse(DataClassORJSONMixin):
    data: InnerData
    success: str
    api: str
    errorMsg: str
