import React from 'react';
import Col from 'react-bootstrap/Col';
import { Container } from 'react-bootstrap';
import Form from 'react-bootstrap/Form';
import Row from 'react-bootstrap/Row';
import InputGroup from 'react-bootstrap/InputGroup';
import Button from 'react-bootstrap/Button';
import { TitleCard, WithEndpoint, useAdapterEndpoint, StatusBox } from 'odin-react';

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

    const [timeFrameValue, setTimeFrameValue] = useState('time');
    const timeFrameRadios = [
      { name: 'Time', value: 'time' },
      { name: 'Frames', value: 'frame'},
      { name: 'Freerun', value: 'free'}
    ];

    return (
      <Container>
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
        <TitleCard title="Acquisition details">
        <Container>
        <Row>
          <Col>
            <Row>
              Measure acq. duration in:
              <ButtonGroup>
                {timeFrameRadios.map((radio, idx) => (
                  <ToggleButton
                    key={idx}
                    id={`radio-${idx}`}
                    type="radio"
                    variant='outline-primary'
                    name="timeFrameRadio"
                    value={radio.value}
                    checked={timeFrameValue === radio.value}
                    onChange={(e) => setTimeFrameValue(e.currentTarget.value)}>
                      {radio.name}
                    </ToggleButton>
                ))}
              </ButtonGroup>
            </Row>
            <Row className="mt-3">
              <InputGroup>
                <InputGroup.Text>
                  Duration (s)
                </InputGroup.Text>
                {timeFrameValue==='time' ? (
                  <EndPointFormControl
                    endpoint={liveXEndPoint}
                    type="number"
                    fullpath={"acquisition/time"}
                    value={liveXEndPoint.data.acquisition?.time}
                    disabled={timeFrameValue==='frame' || timeFrameValue==='free'}
                    style={{border: timeFrameValue==='time' ? '1px solid #00cc00' : undefined}}>
                  </EndPointFormControl>
                ) : (
                  <InputGroup.Text style={{ flex: 1 }}>
                    {liveXEndPoint.data.acquisition?.time}
                  </InputGroup.Text>
                )}
              </InputGroup>
            </Row>
            <Row>
              <InputGroup className="mt-3">
                Timer toggles (no acquisition)
                <EndPointButton
                    endpoint={triggerEndPoint}
                    fullpath={"all_timers_enable"}
                    value={true}
                    event_type="click"
                  >
                    Start all
                  </EndPointButton>
                  <EndPointButton
                    endpoint={triggerEndPoint}
                    fullpath={"all_timers_enable"}
                    value={false}
                    event_type="click"
                    variant='danger'
                  >
                    Stop all
                  </EndPointButton>
              </InputGroup>
            </Row>
          </Col>
          <Col>
            <TitleCard title="Furnace">
              <Row>
                <InputGroup>
                  <InputGroup.Text>
                    Freq. (Hz)
                  </InputGroup.Text>
                  <EndPointFormControl
                    endpoint={liveXEndPoint}
                    type="number"
                    fullpath={"acquisition/frequencies/furnace"}
                    value={triggerEndPoint.data.triggers?.furnace?.frequency}>
                  </EndPointFormControl>
                </InputGroup>
              </Row>
              <Row>
                <InputGroup>
                  <InputGroup.Text>
                    Frame #
                  </InputGroup.Text>
                  {timeFrameValue==='frame' ? (
                  <EndPointFormControl
                    endpoint={liveXEndPoint}
                    type="number"
                    fullpath={"acquisition/frame_target"}
                    value={triggerEndPoint.data.triggers?.furnace?.target}
                    disabled={timeFrameValue==='time' || timeFrameValue==='free'}
                    style={{border: timeFrameValue==='frame' ? '1px solid #00cc00' : undefined}}>
                  </EndPointFormControl>
                  ) : (
                    <InputGroup.Text style={{ flex: 1 }}>
                      {triggerEndPoint.data.triggers?.furnace?.target}
                    </InputGroup.Text>
                  )}
                </InputGroup>
              </Row>
            </TitleCard>
          </Col>
          <Col>
            <TitleCard title="WideFOV">
              <Row>
                <InputGroup style={{
                    display: 'flex',
                    alignItems: 'center',
                    width: '100%'
                  }}>
                  <InputGroup.Text>
                    Freq. (Hz)
                  </InputGroup.Text>
                  <EndPointFormControl
                    endpoint={liveXEndPoint}
                    type="number"
                    fullpath={"acquisition/frequencies/widefov"}
                    value={triggerEndPoint.data.triggers?.widefov?.frequency}>
                  </EndPointFormControl>
                </InputGroup>
              </Row>
              <Row>
                <InputGroup>
                  <InputGroup.Text>
                    Frame #
                  </InputGroup.Text>
                  <InputGroup.Text style={{flex: 1}}>
                  {triggerEndPoint.data.triggers?.widefov?.target}
                  </InputGroup.Text>
                </InputGroup>
              </Row>
            </TitleCard>
          </Col>
          <Col>
            <TitleCard title="NarrowFOV">
              <Row>
                <InputGroup
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    width: '100%'
                  }}>
                  <InputGroup.Text>
                    Freq. (Hz)
                  </InputGroup.Text>
                  <EndPointFormControl
                    endpoint={liveXEndPoint}
                    type="number"
                    fullpath={"acquisition/frequencies/narrowfov"}
                    value={triggerEndPoint.data.triggers?.narrowfov?.frequency}>
                  </EndPointFormControl>
                </InputGroup>
              </Row>
              <Row>
                <InputGroup>
                  <InputGroup.Text>
                    Frame #
                  </InputGroup.Text>
                  <InputGroup.Text style={{flex: 1}}>
                  {triggerEndPoint.data.triggers?.narrowfov?.target}
                  </InputGroup.Text>
                </InputGroup>
              </Row>
            </TitleCard>
          </Col>
        </Row>
        <Row className='mt-3'>
          <Col>
            <StatusBox as="span" label="reading">
                  {checkNullNoDp(furnaceEndPoint.data.tcp?.tcp_reading?.counter)}
            </StatusBox>
          </Col>
          <Col>
            <StatusBox label="Frame count">
              {checkNullNoDp(orcaEndPoint?.data['widefov']?.status.frame_number)}
            </StatusBox>
          </Col>
          </Row>
          <Row>
            <EndPointButton style={{}}
              endpoint={liveXEndPoint}
              fullpath={"acquisition/acquiring"}
              value={liveXEndPoint.data.acquisition?.acquiring ? false : true}
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

