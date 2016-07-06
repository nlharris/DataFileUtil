
package us.kbase.datafileutil;

import java.util.HashMap;
import java.util.Map;
import javax.annotation.Generated;
import com.fasterxml.jackson.annotation.JsonAnyGetter;
import com.fasterxml.jackson.annotation.JsonAnySetter;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonPropertyOrder;
import us.kbase.common.service.UObject;


/**
 * <p>Original spec-file type: FileToShockParams</p>
 * <pre>
 * Input for the file_to_shock function.
 * Required parameters:
 * file_path - the location of the file to load to Shock.
 * Optional parameters:
 * attributes - user-specified attributes to save to the Shock node along
 *     with the file.
 * make_handle - make a Handle Service handle for the shock node. Default
 *     false.
 * </pre>
 * 
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
@Generated("com.googlecode.jsonschema2pojo")
@JsonPropertyOrder({
    "file_path",
    "attributes",
    "make_handle"
})
public class FileToShockParams {

    @JsonProperty("file_path")
    private java.lang.String filePath;
    @JsonProperty("attributes")
    private Map<String, UObject> attributes;
    @JsonProperty("make_handle")
    private Long makeHandle;
    private Map<java.lang.String, Object> additionalProperties = new HashMap<java.lang.String, Object>();

    @JsonProperty("file_path")
    public java.lang.String getFilePath() {
        return filePath;
    }

    @JsonProperty("file_path")
    public void setFilePath(java.lang.String filePath) {
        this.filePath = filePath;
    }

    public FileToShockParams withFilePath(java.lang.String filePath) {
        this.filePath = filePath;
        return this;
    }

    @JsonProperty("attributes")
    public Map<String, UObject> getAttributes() {
        return attributes;
    }

    @JsonProperty("attributes")
    public void setAttributes(Map<String, UObject> attributes) {
        this.attributes = attributes;
    }

    public FileToShockParams withAttributes(Map<String, UObject> attributes) {
        this.attributes = attributes;
        return this;
    }

    @JsonProperty("make_handle")
    public Long getMakeHandle() {
        return makeHandle;
    }

    @JsonProperty("make_handle")
    public void setMakeHandle(Long makeHandle) {
        this.makeHandle = makeHandle;
    }

    public FileToShockParams withMakeHandle(Long makeHandle) {
        this.makeHandle = makeHandle;
        return this;
    }

    @JsonAnyGetter
    public Map<java.lang.String, Object> getAdditionalProperties() {
        return this.additionalProperties;
    }

    @JsonAnySetter
    public void setAdditionalProperties(java.lang.String name, Object value) {
        this.additionalProperties.put(name, value);
    }

    @Override
    public java.lang.String toString() {
        return ((((((((("FileToShockParams"+" [filePath=")+ filePath)+", attributes=")+ attributes)+", makeHandle=")+ makeHandle)+", additionalProperties=")+ additionalProperties)+"]");
    }

}
