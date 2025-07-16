import React from 'react';
import Col from 'react-bootstrap/Col';
import { Container } from 'react-bootstrap';
import Form from 'react-bootstrap/Form';
import Row from 'react-bootstrap/Row';
import InputGroup from 'react-bootstrap/InputGroup';
import Button from 'react-bootstrap/Button';
import { TitleCard, WithEndpoint, useAdapterEndpoint } from 'odin-react';
import { useEffect } from 'react';

import { checkNullNoDp } from '../../utils';

import { useState } from 'react';
import ButtonGroup from 'react-bootstrap/ButtonGroup';
import ToggleButton from 'react-bootstrap/ToggleButton';

const EndPointFormControl = WithEndpoint(Form.Control);
const EndPointButton = WithEndpoint(Button);

function Trigger(props) {

    const {endpoint_url} = props;

    const triggerEndPoint = useAdapterEndpoint('trigger', endpoint_url, 1000);
    const orcaEndPoint = useAdapterEndpoint('camera/cameras/widefov', endpoint_url, 1000);
    const furnaceEndPoint = useAdapterEndpoint('furnace', endpoint_url, 1000);
    const liveXEndPoint = useAdapterEndpoint('livex', endpoint_url, 1000);

    const [timeFrameValue, setTimeFrameValue] = useState('free');
    const timeFrameRadios = [
      { name: 'Run with target', value: 'frame'},
      { name: 'Run endless', value: 'free'}
    ];

    const handleTimeFrameValueChange = (newValue) => {
      setTimeFrameValue(newValue); // update state
      // Put value to endpoint
      let freerunBool = newValue === 'free';
      const sendVal = {['freerun']: freerunBool};
      liveXEndPoint.put(sendVal, 'acquisition');
    }

    const [linkCameras, setLinkCameras] = useState(null);
    useEffect(() => {
      const currentLinks = liveXEndPoint.data?.acquisition?.link_triggers?.current;
      
      const linked = Array.isArray(currentLinks) && currentLinks.length > 0;  // Check if there are linked triggers
      setLinkCameras(linked);
    }, [liveXEndPoint.data?.acquisition?.link_triggers?.current, linkCameras]);

    const handleLinkCamerasChange = (e) => {
      const checked = e.target.checked;
      setLinkCameras(checked);

      const path = checked ? 'acquisition/link_triggers/link_cameras' : 'acquisition/link_triggers/unlink_cameras';
      const value = ['widefov', 'narrowfov'];
      liveXEndPoint.put(value, path);
    }

    const triggers = triggerEndPoint.data?.triggers;
    const ref_trigger = liveXEndPoint.data.acquisition?.reference_trigger;

    const labelWidth = 72;

    return (
      <Container>
        <TitleCard title= {
          <Row>
            <Col xs={3} className="d-flex align-items-center" style={{fontSize:"1.3rem"}}>Trigger settings</Col>
            <Col xs={4}>
              <EndPointButton
                endpoint={triggerEndPoint}
                fullpath={"modbus/reconnect"}
                value={true}
                disabled={triggerEndPoint?.data?.modbus?.connected}
                event_type="click"
                variant={triggerEndPoint.data.modbus?.connected ? "primary": "danger"}
              >
                  {triggerEndPoint.data.modbus?.connected ? "Trigger Connected": "Reconnect Trigger"}
              </EndPointButton>
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
                            event_type="enter"
                            disabled={timeFrameValue==='time' || timeFrameValue==='free'}
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
                    </Row>
                    <Row className="ms-1 me-1">
                      <EndPointButton
                        className="display-inline-block"
                        endpoint={triggerEndPoint}
                        fullpath={`triggers/${key}/enable`}
                        value={triggerEndPoint?.data.triggers[key]?.running ? false : true}
                        disabled={!triggerEndPoint?.data?.modbus?.connected}
                        event_type="click"
                        variant={triggerEndPoint?.data.triggers[key]?.running ? "danger" : "primary"}
                      >
                          {triggerEndPoint?.data.triggers[key]?.running ? "Stop": "Start"}
                      </EndPointButton>
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
                    <EndPointButton
                        endpoint={triggerEndPoint}
                        fullpath={"all_timers_enable"}
                        value={{
                          'enable': true,
                          'freerun': timeFrameValue==='free'
                        }}
                        event_type="click"
                        className="flex-fill"
                      >
                        Start all timers
                      </EndPointButton>
                      <EndPointButton
                        endpoint={triggerEndPoint}
                        fullpath={"all_timers_enable"}
                        value={{
                          'enable': false,
                          'freerun': timeFrameValue==='free'
                        }}
                        event_type="click"
                        variant='danger'
                        className="flex-fill"
                      >
                        Stop all timers
                      </EndPointButton>
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
                    label="Use camera exposure lookup table"
                    className="large-checkbox"
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
                    {checkNullNoDp(furnaceEndPoint.data.tcp?.tcp_reading?.counter)}
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
                    {checkNullNoDp(orcaEndPoint?.data['widefov']?.status.frame_number)}
                  </InputGroup.Text>
                </InputGroup>
              </Col>
            </Row>
            <Row>
              <EndPointButton style={{}}
                endpoint={liveXEndPoint}
                fullpath={liveXEndPoint.data.acquisition?.acquiring ? "acquisition/stop" : "acquisition/start"}
                value={['furnace', 'widefov', 'narrowfov']}
                event_type="click"
                variant={liveXEndPoint.data.acquisition?.acquiring ? "danger" : "success" }>
                  {liveXEndPoint.data.acquisition?.acquiring ? "Stop acquisition" : "Start acquisition"}
              </EndPointButton>
            </Row>
          </Container>
        </TitleCard>
      </Container>
    )
}

export default Trigger;

