
package us.kbase.datafileutil;

import java.util.HashMap;
import java.util.Map;
import javax.annotation.Generated;
import com.fasterxml.jackson.annotation.JsonAnyGetter;
import com.fasterxml.jackson.annotation.JsonAnySetter;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonPropertyOrder;


/**
 * <p>Original spec-file type: FileToShockOutput</p>
 * <pre>
 * Output of the file_to_shock function.
 *     shock_id - the ID of the new Shock node.
 *     handle_id - the handle ID for the new handle, if created. Null
 *        otherwise.
 * </pre>
 * 
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
@Generated("com.googlecode.jsonschema2pojo")
@JsonPropertyOrder({
    "shock_id",
    "handle_id"
})
public class FileToShockOutput {

    @JsonProperty("shock_id")
    private String shockId;
    @JsonProperty("handle_id")
    private String handleId;
    private Map<String, Object> additionalProperties = new HashMap<String, Object>();

    @JsonProperty("shock_id")
    public String getShockId() {
        return shockId;
    }

    @JsonProperty("shock_id")
    public void setShockId(String shockId) {
        this.shockId = shockId;
    }

    public FileToShockOutput withShockId(String shockId) {
        this.shockId = shockId;
        return this;
    }

    @JsonProperty("handle_id")
    public String getHandleId() {
        return handleId;
    }

    @JsonProperty("handle_id")
    public void setHandleId(String handleId) {
        this.handleId = handleId;
    }

    public FileToShockOutput withHandleId(String handleId) {
        this.handleId = handleId;
        return this;
    }

    @JsonAnyGetter
    public Map<String, Object> getAdditionalProperties() {
        return this.additionalProperties;
    }

    @JsonAnySetter
    public void setAdditionalProperties(String name, Object value) {
        this.additionalProperties.put(name, value);
    }

    @Override
    public String toString() {
        return ((((((("FileToShockOutput"+" [shockId=")+ shockId)+", handleId=")+ handleId)+", additionalProperties=")+ additionalProperties)+"]");
    }

}
