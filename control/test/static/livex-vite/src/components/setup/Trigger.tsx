import type { TriggerEndpointTypes, TriggerEndpointTriggerType, CameraEndpointTypes, FurnaceEndpointTypes, LiveXEndpointTypes } from '../../EndpointTypes';

import { Row, Col, Container, Form, InputGroup, ButtonGroup, ToggleButton } from 'react-bootstrap';
import { TitleCard, WithEndpoint, useAdapterEndpoint, EndpointButton } from 'odin-react';
import { useEffect, useState } from 'react';

import { checkNullNoDp } from '../../utils';

const EndPointFormControl = WithEndpoint(Form.Control);

interface TriggerProps {
    endpoint_url: string;
}

function Trigger(props: TriggerProps) {
    const {endpoint_url} = props;

    const triggerEndPoint = useAdapterEndpoint<TriggerEndpointTypes>('trigger', endpoint_url, 1000);
    const orcaEndPoint = useAdapterEndpoint<CameraEndpointTypes>('camera', endpoint_url, 1000);
    const furnaceEndPoint = useAdapterEndpoint<FurnaceEndpointTypes>('furnace', endpoint_url, 1000);
    const liveXEndPoint = useAdapterEndpoint<LiveXEndpointTypes>('livex', endpoint_url, 1000);

    const [timeFrameValue, setTimeFrameValue] = useState('free');
    const timeFrameRadios = [
      { name: 'Run with target', value: 'frame'},
      { name: 'Run endless', value: 'free'}
    ];

    const handleTimeFrameValueChange = (newValue: string) => {
      setTimeFrameValue(newValue); // update state
      // Put value to endpoint
      let freerunBool = newValue === 'free';
      const sendVal = {['freerun']: freerunBool};
      liveXEndPoint.put(sendVal, 'acquisition');
    }

    const [linkCameras, setLinkCameras] = useState(false);
    useEffect(() => {
      const currentLinks = liveXEndPoint.data?.acquisition?.link_triggers?.current;

      const linked = Array.isArray(currentLinks) && currentLinks.length > 0;  // Check if there are linked triggers
      setLinkCameras(linked);
    }, [liveXEndPoint.data?.acquisition?.link_triggers?.current]);

    const handleLinkCamerasChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const checked = e.target.checked;
      setLinkCameras(checked);

      const pathHead = checked ? 'link_cameras' : 'unlink_cameras';
      const pathBody = "acquisition/link_triggers/";
      const value = ['widefov', 'narrowfov'];
      liveXEndPoint.put({[pathHead]: value}, pathBody);
    }

    const [exposureLookup, setExposureLookup] = useState(false);
    useEffect(() => {
      const usingLookup = liveXEndPoint.data?.cameras?.use_exposure_lookup ?? false;
      setExposureLookup(usingLookup);
    }, [liveXEndPoint.data?.cameras?.use_exposure_lookup]);

    const handleExposureLookupChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const checked = e.target.checked;
      setExposureLookup(checked);

      const path = 'cameras/';
      const value = checked ? true : false;  // Put false to disable if checked (enabled)
      liveXEndPoint.put({ 'use_exposure_lookup': value }, path);
    }

    const triggers = triggerEndPoint.data?.triggers;
    const ref_trigger = liveXEndPoint?.data?.acquisition?.reference_trigger;

    const labelWidth = 72;

    return (
      <Container>
        <TitleCard title= {
          <Row>
            <Col xs={3} className="d-flex align-items-center" style={{fontSize:"1.3rem"}}>Trigger settings</Col>
            <Col xs={4}>
              <EndpointButton
                endpoint={triggerEndPoint}
                fullpath={"modbus/reconnect"}
                value={true}
                disabled={triggerEndPoint?.data?.modbus?.connected}
                variant={triggerEndPoint?.data?.modbus?.connected ? "primary": "danger"}
              >
                  {triggerEndPoint?.data?.modbus?.connected ? "Trigger Connected": "Reconnect Trigger"}
              </EndpointButton>
            </Col>
          </Row>
          }>
          <Container>
            <Row>
              {triggers && Object.entries(triggers).map(([key, data]) => (
                <Col key={key}>
                  <TitleCard title={key}>
                    <Row>
                      <InputGroup>
                        <InputGroup.Text>Freq. (Hz)</InputGroup.Text>
                        <EndPointFormControl
                          endpoint={liveXEndPoint}
                          type="number"
                          fullpath={`acquisition/frequencies/${key}`}
                          event_type="enter">
                        </EndPointFormControl>
                      </InputGroup>
                    </Row>
                    <Row>
                      <InputGroup>
                        <InputGroup.Text>Frame #</InputGroup.Text>
                        {timeFrameValue==='frame' && key===ref_trigger ? (
                          <EndPointFormControl
                            endpoint={liveXEndPoint}
                            type="number"
                            fullpath={'acquisition/frame_target'}
                            style={{
                              border: timeFrameValue==='frame' ? '1px solid #00cc00' : undefined
                            }}
                            />
                        ) : (
                          <InputGroup.Text style={{flex:1}}>
                            {data.target}
                          </InputGroup.Text>
                        )}
                      </InputGroup>
                      {orcaEndPoint?.data?.cameras?.hasOwnProperty(key) && (
                        <InputGroup>
                          <InputGroup.Text>Exposure</InputGroup.Text>
                          <EndPointFormControl
                            endpoint={liveXEndPoint}
                            type="number"
                            fullpath={`cameras/${key}_exposure`}
                            event_type="enter"
                          />
                        </InputGroup>
                      )}
                    </Row>
                    <Row className="ms-1 me-1">
                      <EndpointButton
                        className="display-inline-block"
                        endpoint={triggerEndPoint}
                        fullpath={`triggers/${key}/enable`}
                        value={triggerEndPoint?.data?.triggers?.[key]?.running ? false : true}
                        disabled={!triggerEndPoint?.data?.modbus?.connected}
                        variant={triggerEndPoint?.data?.triggers?.[key]?.running ? "danger" : "primary"}
                      >
                          {triggerEndPoint?.data?.triggers?.[key]?.running ? "Stop": "Start"}
                      </EndpointButton>
                    </Row>
                  </TitleCard>
                </Col>
              ))}
            </Row>
            <Row>
              <Col xs={12} sm={4} className="mt-3 mb-3">
                <Row>
                  <ButtonGroup className='d-flex'>
                    {timeFrameRadios.map((radio, idx) => (
                      <ToggleButton
                        key={idx}
                        className='equal-width-buttongroup'
                        id={`radio-${idx}`}
                        type="radio"
                        variant='outline-primary'
                        name="timeFrameRadio"
                        value={radio.value}
                        checked={timeFrameValue === radio.value}
                        onChange={(e) => handleTimeFrameValueChange(e.currentTarget.value)}>
                          {radio.name}
                        </ToggleButton>
                    ))}
                  </ButtonGroup>
                </Row>
                <Row className='mt-3'>
                  <InputGroup>
                    <EndpointButton
                        endpoint={triggerEndPoint}
                        fullpath={"all_timers_enable"}
                        value={{
                          'enable': true,
                          'freerun': timeFrameValue==='free'
                        }}
                        className="flex-fill"
                      >
                        Start all timers
                      </EndpointButton>
                      <EndpointButton
                        endpoint={triggerEndPoint}
                        fullpath={"all_timers_enable"}
                        value={{
                          'enable': false,
                          'freerun': timeFrameValue==='free'
                        }}
                        variant='danger'
                        className="flex-fill"
                      >
                        Stop all timers
                      </EndpointButton>
                  </InputGroup>
                </Row>
              </Col>
              <Col xs={6}>
                <Row className='mt-3'>
                  <Form.Check
                    type="checkbox"
                    label="Link camera frequencies and exposures"
                    className="large-checkbox"
                    checked={linkCameras}
                    onChange={handleLinkCamerasChange}
                  />
                </Row>
                <Row className='mt-4'>
                  <Form.Check
                    type="checkbox"
                    label="Lookup cam exposure from frequency"
                    className="large-checkbox"
                    checked={exposureLookup}
                    onChange={handleExposureLookupChange}
                  />
                </Row>
              </Col>
            </Row>
            <Row className='mt-3 mb-3'>
              <Col>
                <InputGroup>
                  <InputGroup.Text>PLC Reading Counter</InputGroup.Text>
                  <InputGroup.Text style={{
                    width: labelWidth,
                    border: '1px solid lightblue',
                    backgroundColor: '#e0f7ff'
                  }}>
                    {checkNullNoDp(furnaceEndPoint.data?.tcp?.tcp_reading?.frame)}
                  </InputGroup.Text>
                </InputGroup>
              </Col>
              <Col>
                <InputGroup>
                  <InputGroup.Text>widefov frame count</InputGroup.Text>
                  <InputGroup.Text style={{
                    width: labelWidth,
                    border: '1px solid lightblue',
                    backgroundColor: '#e0f7ff'
                  }}>
                    {checkNullNoDp(orcaEndPoint?.data?.widefov?.status?.frame_number)}
                  </InputGroup.Text>
                </InputGroup>
              </Col>
              <Col>
                <InputGroup>
                  <InputGroup.Text>narrowfov frame count</InputGroup.Text>
                  <InputGroup.Text style={{
                    width: labelWidth,
                    border: '1px solid lightblue',
                    backgroundColor: '#e0f7ff'
                  }}>
                    {checkNullNoDp(orcaEndPoint?.data?.narrowfov?.status?.frame_number)}
                  </InputGroup.Text>
                </InputGroup>
              </Col>
            </Row>
            <Row>
              <EndpointButton style={{}}
                endpoint={liveXEndPoint}
                fullpath={liveXEndPoint.data?.acquisition?.acquiring ? "acquisition/stop" : "acquisition/start"}
                value={['furnace', 'widefov', 'narrowfov']}
                variant={liveXEndPoint.data?.acquisition?.acquiring ? "danger" : "success" }>
                  {liveXEndPoint.data?.acquisition?.acquiring ? "Stop acquisition" : "Start acquisition"}
              </EndpointButton>
            </Row>
          </Container>
        </TitleCard>
      </Container>
    )
}

export default Trigger;

