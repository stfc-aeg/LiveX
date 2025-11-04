import React from 'react';
import { useState, useRef, useEffect } from 'react';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';
import { Container, Stack } from 'react-bootstrap';
import Form from 'react-bootstrap/Form';
import InputGroup from 'react-bootstrap/InputGroup';
import { useAdapterEndpoint, WithEndpoint, TitleCard } from 'odin-react';
import Button from 'react-bootstrap/Button';
import { FloatingLabel } from 'react-bootstrap';

import { checkNullNoDp, floatingInputStyle, floatingLabelStyle } from '../../utils';

import ClickableImage from './ClickableImage';

const EndPointFormControl = WithEndpoint(Form.Control);
const EndPointButton = WithEndpoint(Button);

function OrcaCamera(props) {
    const {endpoint} = props;
    const {endpoint_url} = props;
    const {name} = props;
    const {connectedPuttingDisable} = props;
 
    const liveViewEndPoint = useAdapterEndpoint('live_data', endpoint_url, 1000);
    const liveViewData = liveViewEndPoint?.data[name];

    const colour_metadata = liveViewEndPoint?.metadata[name]?.image.colour;

    // Array of camera status names
    const status = ['disconnected', 'connected', 'capturing'];
    // Current status of orcaCamera (for readability)
    const orcaStatus = endpoint?.data[name]?.status?.camera_status;
    const orcaConnected = endpoint?.data[name]?.connection?.connected;

    // This dropdown behaves differently so that you could enter other resolutions via command
    const commonImageResolutions = [
        10, 25, 50, 75, 100
    ];

  const [fitMode, setFitMode] = useState(false);
  const [fitHeightFactor, setFitHeightFactor] = useState(7); // default 70vh
  const [aspectRatio, setAspectRatio] = useState(null);

  const wrapperRef = useRef(null);

  // measure image to get its aspect ratio
  useEffect(() => {
    const wrapper = wrapperRef.current;
    if (!wrapper) return;

    const img = wrapper.querySelector("img");
    if (!img) return;

    const updateAspect = () => {
      if (img.naturalWidth && img.naturalHeight) {
        setAspectRatio(img.naturalWidth / img.naturalHeight);
      }
    };

    // wait for image to load
    img.addEventListener("load", updateAspect);
    updateAspect();

    return () => img.removeEventListener("load", updateAspect);
  }, [liveViewData]);

  // compute container style
  const fitStyle =
    fitMode && aspectRatio
      ? {
          height: `${fitHeightFactor * 10}vh`,
          width: `${fitHeightFactor*10 * aspectRatio}vh`,
          maxWidth: "100%",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
        }
      : {
          width: "100%",
          height: "auto",
          display: "flex",
          justifyContent: "center",
        };


    /* The titlecard buttons have variable output, display, and colour, depending on the camera status.
    Example, when the camera isn't connected, you can connect. If it's connected, you can disconnect.
    When capturing, that button is disabled - you need to move it out of that state first.*/
    return (
        <Container>
          <TitleCard title={
            <Row>
              <Col xs={4} className="d-flex align-items-center" style={{fontSize:'1.3rem'}}>
                {endpoint?.data[name]?.camera_name + " control"}
              </Col>
              <Col>
                {orcaConnected ? (
                <Row>
                  <Col xs={3}>
                    <EndPointButton // Move between statuses 1 and 0
                      endpoint={endpoint}
                      value={orcaStatus!==status[0] ? "disconnect" : "connect"}
                      fullpath={`${name}/command`}
                      event_type="click"
                      disabled={![status[1], status[0]].includes(orcaStatus)}
                      variant={orcaStatus!==status[0] ? "warning" : "success"}>
                        {orcaStatus!==status[0] ? 'Disconnect' : 'Connect'}
                    </EndPointButton>
                  </Col>
                  <Col xs={3}>
                    <EndPointButton // Move between statuses 3 and 1
                      endpoint={endpoint}
                      value={orcaStatus===status[2] ? "end_capture" : "capture"}
                      fullpath={`${name}/command`}
                      event_type="click"
                      disabled={![status[2], status[1]].includes(orcaStatus)}
                      variant={orcaStatus===status[2] ? "warning" : "success"}>
                      {orcaStatus===status[2] ? 'Stop Capturing' : 'Capture'}
                    </EndPointButton>
                  </Col>
                </Row>
                ) : (
                <Col>
                  <EndPointButton
                    endpoint={endpoint}
                    value={true}
                    fullpath={`${name}/connection/reconnect`}
                    event_type="click"
                    disabled={orcaConnected}
                    variant={orcaConnected ? "info" : "danger"}>
                    {orcaConnected ? 'Connected' : 'Reconnect'}
                  </EndPointButton>
                </Col>
                )}
              </Col>
            </Row>
          }>
            <Col>
              <Row className="mb-3">
                <Col xs={4}>
                  <FloatingLabel
                    label="Status">
                      <Form.Control
                        plaintext
                        readOnly
                        style={floatingLabelStyle}
                        value={(orcaStatus || "Not found")}
                      />
                  </FloatingLabel>
                </Col>
                <Col xs={4}>
                  <FloatingLabel
                    label="Frame Count">
                      <Form.Control
                        plaintext
                        readOnly
                        style={floatingLabelStyle}
                        value={checkNullNoDp(endpoint?.data[name]?.status.frame_number)}
                      />
                  </FloatingLabel>
                </Col>
                <Col xs={4}>
                  <FloatingLabel
                    label="Cam Temp. (C)">
                      <Form.Control
                        plaintext
                        readOnly
                        style={floatingLabelStyle}
                        value={checkNullNoDp(endpoint?.data[name]?.status?.camera_temperature || "Not found")}
                      />
                  </FloatingLabel>
                </Col>
              </Row>
              <Stack>
              <InputGroup>
                <InputGroup.Text>
                    exposure_time
                </InputGroup.Text>
                <EndPointFormControl
                    endpoint={endpoint}
                    type="number"
                    fullpath={`${name}/config/exposure_time`}
                    event_type="enter"
                    disabled={connectedPuttingDisable}>
                </EndPointFormControl>
              </InputGroup>
              </Stack>
              <TitleCard title={
                <Row>
                  <Col xs={4} className='d-flex align-items-center' style={{fontSize:'1.3rem'}}>
                    {`${endpoint?.data[name]?.camera_name} preview`}
                  </Col>
                  <Col xs={8} className='d-flex justify-content-end'>
                    <Form.Text>Fix height scale</Form.Text>
                    <Form.Range
                      min={1}
                      max={10}
                      step={1}
                      value={fitHeightFactor}
                      onChange={(e) => setFitHeightFactor(Number(e.target.value))}
                      style={{ width: "120px" }}
                    />
                    <Button
                      variant={fitMode?"danger":"primary"}
                      onClick={()=>setFitMode(!fitMode)}>
                        {fitMode?"Auto image height":"Fix image height"}
                    </Button>
                  </Col>
                </Row>}>
                <Row className={fitMode?"justify-content-center":null}>
                  <div ref={wrapperRef} style={fitMode?{
                    ...fitStyle,
                    lineHeight:0, verticalAlign:'top'
                    }:null}>
                    <ClickableImage
                      id={`image-${name}`}
                      endpoint={liveViewEndPoint}
                      imgPath={`_image/${name}/image`}
                      coordsPath={`${name}/image`}
                      coordsParam="zoom"
                      valuesAsPercentages={true}>
                    </ClickableImage>
                  </div>

                </Row>
                <Row>
                  <ClickableImage
                    id={`histogram-${name}`}
                    endpoint={liveViewEndPoint}
                    imgPath={`_image/${name}/histogram`}
                    coordsPath={`${name}/image`}
                    coordsParam="clip_range_percent"
                    maximiseAxis="y"
                    rectOutlineColour='black'
                    rectRgbaProperties='rgba(50,50,50,0.05)'
                    valuesAsPercentages={true}>
                  </ClickableImage>
                </Row>
                <Row className="mt-3">
                  <Col xs={12} sm={6} style={{justifyContent:'center'}}>
                    <Row style={{justifyContent:'center'}}>
                        <EndPointButton className="mb-3 w-75"
                          endpoint={liveViewEndPoint}
                          fullpath={`${name}/image/autoclip`}
                          value={liveViewData?.image?.autoclip ? false : true}
                          variant={liveViewData?.image.autoclip ? 'danger' : 'primary'}>
                          {liveViewData?.image?.autoclip ? "Disable Autoclip" : "Enable Autoclip"}
                        </EndPointButton>
                    </Row>
                    <FloatingLabel className="mb-3"
                    label="Autoclip %">
                      <EndPointFormControl
                          endpoint={liveViewEndPoint}
                          type="number"
                          fullpath={`${name}/image/autoclip_percent`}
                          disabled={connectedPuttingDisable}>
                      </EndPointFormControl>
                    </FloatingLabel>
                  </Col>
                  <Col xs={12} sm={6}>
                      <Row style={{justifyContent:'center'}}>
                        <EndPointButton className="mt-2 mb-3 w-75"
                          endpoint={liveViewEndPoint}
                          fullpath={`${name}/image/clip_range_value`}
                          value={[0, 65535]}
                          variant="primary">
                          Reset Clipping Range
                        </EndPointButton>
                      </Row>
                      <Row style={{justifyContent:'center'}}>
                        <EndPointButton className="w-75"
                          endpoint={liveViewEndPoint}
                          fullpath={`${name}/image/zoom`}
                          value={[[0, 100], [0, 100]]}
                          variant="primary">
                            Reset Zoom
                        </EndPointButton>
                      </Row>
                  </Col>
                </Row>
                <Row className="mt-3">
                  <Col xs={6}>
                    <FloatingLabel
                      label="Image Colour Map">
                      <Form.Select
                        style={floatingInputStyle}
                        value={liveViewData?.image?.colour ?? "?"}
                        onChange={(e)=> {
                          liveViewEndPoint.put(e.target.value, `${name}/image/colour`);
                        }}>
                          {(colour_metadata?.allowed_values || ['greyscale']).map(
                            (selection, index) => (
                              <option value={selection} key={index}>{selection}</option>
                            )
                          )}
                      </Form.Select>
                    </FloatingLabel>
                  </Col>
                  <Col xs={6}>
                    <FloatingLabel
                      label="Resolution (%)">
                        <Form.Select
                          style={floatingInputStyle}
                          value={liveViewData?.image?.resolution ?? "?"}
                          onChange={(e)=> {
                            liveViewEndPoint.put(e.target.value, `${name}/image/resolution`);
                          }}>
                            {commonImageResolutions.map((effect, index) => (
                              <option value={effect} key={index}>
                                {effect}
                              </option>
                              ))
                            }
                        </Form.Select>
                    </FloatingLabel>
                  </Col>
                </Row>
              </TitleCard>
            </Col>
          </TitleCard>
        </Container>
    )
}

export default OrcaCamera;

