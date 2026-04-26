package br.gov.educacao.sp.pecobservation.adapters.network

import br.gov.educacao.sp.pecobservation.BuildConfig
import br.gov.educacao.sp.pecobservation.domain.errors.NetworkError
import br.gov.educacao.sp.pecobservation.ports.NetworkClientPort
import com.google.gson.Gson
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.logging.HttpLoggingInterceptor
import java.io.File
import java.util.concurrent.TimeUnit
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class RetrofitNetworkClient @Inject constructor(
    private val tokenStore: TokenStore,
) : NetworkClientPort {

    private val gson = Gson()

    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(120, TimeUnit.SECONDS)
        .writeTimeout(120, TimeUnit.SECONDS)
        .addInterceptor { chain ->
            val token = tokenStore.accessToken
            val req = if (token != null) {
                chain.request().newBuilder()
                    .addHeader("Authorization", "Bearer $token")
                    .build()
            } else {
                chain.request()
            }
            chain.proceed(req)
        }
        .addInterceptor(HttpLoggingInterceptor().apply {
            level = if (BuildConfig.DEBUG) HttpLoggingInterceptor.Level.BODY
                    else HttpLoggingInterceptor.Level.NONE
        })
        .build()

    private val baseUrl = BuildConfig.API_BASE_URL

    override suspend fun post(path: String, body: Map<String, Any>): Map<String, Any> =
        withContext(Dispatchers.IO) {
            val json = gson.toJson(body)
            val request = Request.Builder()
                .url("$baseUrl$path")
                .post(json.toRequestBody("application/json".toMediaType()))
                .build()
            execute(request)
        }

    override suspend fun get(path: String): Map<String, Any> =
        withContext(Dispatchers.IO) {
            val request = Request.Builder()
                .url("$baseUrl$path")
                .get()
                .build()
            execute(request)
        }

    override suspend fun patch(path: String, body: Map<String, Any>): Map<String, Any> =
        withContext(Dispatchers.IO) {
            val json = gson.toJson(body)
            val request = Request.Builder()
                .url("$baseUrl$path")
                .patch(json.toRequestBody("application/json".toMediaType()))
                .build()
            execute(request)
        }

    override suspend fun putBinary(url: String, filePath: String, contentType: String) =
        withContext(Dispatchers.IO) {
            val file = File(filePath)
            val request = Request.Builder()
                .url(url)
                .put(file.asRequestBody(contentType.toMediaType()))
                .build()
            execute(request)
            Unit
        }

    @Suppress("UNCHECKED_CAST")
    private fun execute(request: Request): Map<String, Any> {
        val response = client.newCall(request).execute()
        val body = response.body?.string() ?: "{}"
        return when {
            response.isSuccessful -> gson.fromJson(body, Map::class.java) as Map<String, Any>
            response.code == 401  -> throw NetworkError.Unauthorized()
            response.code == 404  -> throw NetworkError.NotFound(request.url.encodedPath)
            else                  -> throw NetworkError.ServerError(response.code, body)
        }
    }
}
