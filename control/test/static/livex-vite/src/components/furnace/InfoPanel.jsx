import React from 'react';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';
import InputGroup from 'react-bootstrap/InputGroup';
import { TitleCard } from 'odin-react';
import { checkNull, usePrevious } from '../../utils';
import { Form } from 'react-bootstrap';

import { floatingLabelStyle } from '../../utils';
import { FloatingLabel } from 'react-bootstrap';

function InfoPanel(props) {
    const {furnaceEndPoint} = props;

    const lastInput_a = usePrevious(furnaceEndPoint.data?.pid_a?.temperature);
    const lastInput_b = usePrevious(furnaceEndPoint.data?.pid_b?.temperature);

    // Fixing the label width of the display labels so that they're consistent
    // ~6px per character.
    const labelWidth = 80;
    const valueWidth = 60;

    const labelStyling = {
        width: valueWidth,
        border: '1px solid lightblue',
        backgroundColor: '#e0f7ff'
      }

  return (
    <TitleCard title={
      <Row>
        <Col xs={3} className="d-flex align-items-center" style={{fontSize:'1.3rem'}}>Monitor Panel</Col>
      </Row>
    }>
      <Row>
        <label>Extra Thermocouples</label>
        <Col xs={6}>
          <FloatingLabel
            label="Thermo C">
              <Form.Control
                plaintext
                readOnly
                style={floatingLabelStyle}
                value={checkNull(furnaceEndPoint.data?.thermocouples?.thermocouple_c?.value)}
              />
          </FloatingLabel>
          <FloatingLabel
            label="Thermo D">
              <Form.Control
                plaintext
                readOnly
                style={floatingLabelStyle}
                value={checkNull(furnaceEndPoint.data?.thermocouples?.thermocouple_d?.value)}
              />
          </FloatingLabel>
        </Col>
        <Col>
          <FloatingLabel
            label="Thermo E">
              <Form.Control
                plaintext
                readOnly
                style={floatingLabelStyle}
                value={checkNull(furnaceEndPoint.data?.thermocouples?.thermocouple_e?.value)}
              />
          </FloatingLabel>
          <FloatingLabel
            label="Thermo f">
              <Form.Control
                plaintext
                readOnly
                style={floatingLabelStyle}
                value={checkNull(furnaceEndPoint.data?.thermocouples?.thermocouple_f?.value)}
              />
          </FloatingLabel>
        </Col>
      </Row>
      <Row className="mt-3">
        <Col xs={4}>
          <label>PID A</label>
          <Row>
            <FloatingLabel
              label="PID % Out">
                <Form.Control
                  plaintext
                  readOnly
                  style={floatingLabelStyle}
                  value={checkNull(furnaceEndPoint.data?.pid_a?.output)}
                />
            </FloatingLabel>
          </Row>
          <Row>
            <FloatingLabel
              label="PLC Volt.">
                <Form.Control
                  plaintext
                  readOnly
                  style={floatingLabelStyle}
                  value={checkNull((furnaceEndPoint.data?.pid_a?.output) * 0.1 * 0.8)}
                />
            </FloatingLabel>
          </Row>
          <Row className="mt-3">
            <FloatingLabel
              label="P Gain">
                <Form.Control
                  plaintext
                  readOnly
                  style={floatingLabelStyle}
                  value={checkNull(
                  furnaceEndPoint.data.pid_a?.proportional
                  * (furnaceEndPoint.data.pid_a?.setpoint - furnaceEndPoint.data.pid_a?.temperature))}
                />
            </FloatingLabel>
          </Row>
          <Row>
            <FloatingLabel
              label="I Sum Diff.">
                <Form.Control
                  plaintext
                  readOnly
                  style={floatingLabelStyle}
                  value={checkNull(
                  furnaceEndPoint.data.pid_a?.integral
                  * (furnaceEndPoint.data.pid_a?.setpoint - furnaceEndPoint.data.pid_a?.temperature))}
                />
            </FloatingLabel>
          </Row>
          <Row>
            <FloatingLabel
              label="D Sum Diff.">
                <Form.Control
                  plaintext
                  readOnly
                  style={floatingLabelStyle}
                  value={checkNull(
                  furnaceEndPoint.data.pid_a?.derivative
                  * (furnaceEndPoint.data.pid_a?.temperature - lastInput_a))}
                />
            </FloatingLabel>
          </Row>
          <Row>
            <FloatingLabel
              label="PID Out Sum">
                <Form.Control
                  plaintext
                  readOnly
                  style={floatingLabelStyle}
                  value={checkNull(furnaceEndPoint.data.pid_a?.outputsum)}
                />
            </FloatingLabel>
          </Row>
        </Col>


        <Col xs={4}>
          <label>PID B</label>
          <Row>
            <FloatingLabel
              label="PID % Out">
                <Form.Control
                  plaintext
                  readOnly
                  style={floatingLabelStyle}
                  value={checkNull(furnaceEndPoint.data?.pid_b?.output)}
                />
            </FloatingLabel>
            </Row>
            <Row>
              <FloatingLabel
                label="PLC Volt.">
                  <Form.Control
                    plaintext
                    readOnly
                    style={floatingLabelStyle}
                    value={checkNull((furnaceEndPoint.data?.pid_b?.output) * 0.1 * 0.8)}
                  />
              </FloatingLabel>
            </Row>
          <Row className="mt-3">
            <FloatingLabel
              label="P Gain">
                <Form.Control
                  plaintext
                  readOnly
                  style={floatingLabelStyle}
                  value={checkNull(
                  furnaceEndPoint.data.pid_b?.proportional
                  * (furnaceEndPoint.data.pid_b?.setpoint - furnaceEndPoint.data.pid_b?.temperature))}
                />
            </FloatingLabel>
          </Row>
          <Row>
            <FloatingLabel
              label="I Sum Diff.">
                <Form.Control
                  plaintext
                  readOnly
                  style={floatingLabelStyle}
                  value={checkNull(
                  furnaceEndPoint.data.pid_b?.integral
                  * (furnaceEndPoint.data.pid_b?.setpoint - furnaceEndPoint.data.pid_b?.temperature))}
                />
            </FloatingLabel>
          </Row>
          <Row>
            <FloatingLabel
              label="D Sum Diff.">
                <Form.Control
                  plaintext
                  readOnly
                  style={floatingLabelStyle}
                  value={checkNull(
                  furnaceEndPoint.data.pid_b?.derivative
                  * (furnaceEndPoint.data.pid_b?.temperature - lastInput_b))}
                />
            </FloatingLabel>
          </Row>
          <Row>
            <FloatingLabel
              label="Pid Out Sum">
                <Form.Control
                  plaintext
                  readOnly
                  style={floatingLabelStyle}
                  value={checkNull(furnaceEndPoint.data.pid_b?.outputsum)}
                />
            </FloatingLabel>
          </Row>
        </Col>

      </Row>
    </TitleCard>
  )
}
export default InfoPanel;