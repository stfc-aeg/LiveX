import React from 'react';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';
import InputGroup from 'react-bootstrap/InputGroup';
import { TitleCard, useAdapterEndpoint } from 'odin-react';
import { checkNull, usePrevious } from '../../utils';

function InfoPanel(props) {
    const {furnaceEndPoint} = props;

    const lastInput_a = usePrevious(furnaceEndPoint.data?.pid_upper?.temperature);
    const lastInput_b = usePrevious(furnaceEndPoint.data?.pid_lower?.temperature);

    // Fixing the label width of the display labels so that they're consistent
    // ~6px per character.
    const labelWidth = 80;
    const valueWidth = 65;

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
        <Col xs={4} md={6} xl={4}>
          <InputGroup>
            <InputGroup.Text style={{width:labelWidth}}>
              {furnaceEndPoint.data?.thermocouples?.thermocouple_extra_1?.label ? furnaceEndPoint.data?.thermocouples?.thermocouple_extra_1?.label : 'Not in use'}
            </InputGroup.Text>
            <InputGroup.Text
              style={labelStyling}>
                {checkNull(furnaceEndPoint.data?.thermocouples?.thermocouple_extra_1?.value)}
              </InputGroup.Text>
          </InputGroup>
          <InputGroup>
            <InputGroup.Text style={{width:labelWidth}}>
              {furnaceEndPoint.data?.thermocouples?.thermocouple_extra_2?.label ? furnaceEndPoint.data?.thermocouples?.thermocouple_extra_2?.label : 'Not in use'}
            </InputGroup.Text>
            <InputGroup.Text
              style={labelStyling}>
                {checkNull(furnaceEndPoint.data?.thermocouples?.thermocouple_extra_2?.value)}
                </InputGroup.Text>
          </InputGroup>
        </Col>
        <Col xs={4} md={6} xl={4}>
          <InputGroup>
            <InputGroup.Text style={{width:labelWidth}}>
              {furnaceEndPoint.data?.thermocouples?.thermocouple_extra_3?.label ? furnaceEndPoint.data?.thermocouples?.thermocouple_extra_3?.label : 'Not in use'}
            </InputGroup.Text>
            <InputGroup.Text
              style={labelStyling}>
                {checkNull(furnaceEndPoint.data?.thermocouples?.thermocouple_extra_3?.value)}
                </InputGroup.Text>
          </InputGroup>
          <InputGroup>
            <InputGroup.Text style={{width:labelWidth}}>
              {furnaceEndPoint.data?.thermocouples?.thermocouple_extra_4?.label ? furnaceEndPoint.data?.thermocouples?.thermocouple_extra_4?.label : 'Not in use'}
            </InputGroup.Text>
            <InputGroup.Text
              style={labelStyling}>
                {checkNull(furnaceEndPoint.data?.thermocouples?.thermocouple_extra_4?.value)}
                </InputGroup.Text>
          </InputGroup>
        </Col>
      </Row>
      <Row className="mt-3">
        <Col xs={6} xl={4}>
          <label>PID A</label>
          <Row>
            <InputGroup>
              <InputGroup.Text style={{width:labelWidth}}>
                PID % Out
              </InputGroup.Text>
              <InputGroup.Text
                style={labelStyling}>
                  {checkNull(furnaceEndPoint.data?.pid_upper?.output)}
              </InputGroup.Text>
            </InputGroup>
            </Row>
            <Row>
              <InputGroup>
                <InputGroup.Text style={{width:labelWidth}}>
                  PLC Volt.
                </InputGroup.Text>
                <InputGroup.Text
                  style={labelStyling}>
                    {checkNull((furnaceEndPoint.data?.pid_upper?.output) * 0.1)}
                </InputGroup.Text>
              </InputGroup>
            </Row>
          <Row className="mt-3">
            <InputGroup>
              <InputGroup.Text style={{width:labelWidth}}>
                P Gain
              </InputGroup.Text>
              <InputGroup.Text style={labelStyling}>
                {checkNull(
                  furnaceEndPoint.data.pid_upper?.proportional
                  * (furnaceEndPoint.data.pid_upper?.setpoint - furnaceEndPoint.data.pid_upper?.temperature))}
              </InputGroup.Text>
            </InputGroup>
          </Row>
          <Row>
            <InputGroup>
              <InputGroup.Text style={{width:labelWidth}}>
                I Sum Diff.
              </InputGroup.Text>
              <InputGroup.Text style={labelStyling}>
                {checkNull(
                  furnaceEndPoint.data.pid_upper?.integral
                  * (furnaceEndPoint.data.pid_upper?.setpoint - furnaceEndPoint.data.pid_upper?.temperature))}
              </InputGroup.Text>
            </InputGroup>
          </Row>
          <Row>
            <InputGroup>
              <InputGroup.Text style={{width:labelWidth}}>
                D Sum Diff.
              </InputGroup.Text>
              <InputGroup.Text style={labelStyling}>
              {checkNull(
                  furnaceEndPoint.data.pid_upper?.derivative
                  * (furnaceEndPoint.data.pid_upper?.temperature - lastInput_a))}
              </InputGroup.Text>
            </InputGroup>
          </Row>
          <Row>
            <InputGroup>
              <InputGroup.Text style={{width:labelWidth}}>
                Out Sum
              </InputGroup.Text>
              <InputGroup.Text style={labelStyling}>
              {checkNull(furnaceEndPoint.data.pid_upper?.outputsum)}
              </InputGroup.Text>
            </InputGroup>
          </Row>
        </Col>
        <Col xs={6} xl={4}>
          <label>PID B</label>
          <Row>
            <InputGroup>
              <InputGroup.Text style={{width:labelWidth}}>
                PID % Out
              </InputGroup.Text>
              <InputGroup.Text
                style={labelStyling}>
                  {checkNull(furnaceEndPoint.data?.pid_lower?.output)}
              </InputGroup.Text>
            </InputGroup>
            </Row>
            <Row>
              <InputGroup>
                <InputGroup.Text style={{width:labelWidth}}>
                  PLC Volt.
                </InputGroup.Text>
                <InputGroup.Text
                  style={labelStyling}>
                    {checkNull((furnaceEndPoint.data?.pid_lower?.output) * 0.1)}
                </InputGroup.Text>
              </InputGroup>
            </Row>
          <Row className="mt-3">
            <InputGroup>
              <InputGroup.Text style={{width:labelWidth}}>
                P Gain
              </InputGroup.Text>
              <InputGroup.Text style={labelStyling}>
                {checkNull(
                  furnaceEndPoint.data.pid_lower?.proportional
                  * (furnaceEndPoint.data.pid_lower?.setpoint - furnaceEndPoint.data.pid_lower?.temperature))}
              </InputGroup.Text>
            </InputGroup>
          </Row>
          <Row>
            <InputGroup>
              <InputGroup.Text style={{width:labelWidth}}>
                I Sum Diff.
              </InputGroup.Text>
              <InputGroup.Text style={labelStyling}>
                {checkNull(
                  furnaceEndPoint.data.pid_lower?.integral
                  * (furnaceEndPoint.data.pid_lower?.setpoint - furnaceEndPoint.data.pid_lower?.temperature))}
              </InputGroup.Text>
            </InputGroup>
          </Row>
          <Row>
            <InputGroup>
              <InputGroup.Text style={{width:labelWidth}}>
                D Sum Diff.
              </InputGroup.Text>
              <InputGroup.Text style={labelStyling}>
              {checkNull(
                  furnaceEndPoint.data.pid_lower?.derivative
                  * (furnaceEndPoint.data.pid_lower?.temperature - lastInput_b))}
              </InputGroup.Text>
            </InputGroup>
          </Row>
          <Row>
            <InputGroup>
              <InputGroup.Text style={{width:labelWidth}}>
                Out Sum
              </InputGroup.Text>
              <InputGroup.Text style={labelStyling}>
              {checkNull(furnaceEndPoint.data.pid_lower?.outputsum)}
              </InputGroup.Text>
            </InputGroup>
          </Row>
        </Col>
      </Row>
    </TitleCard>
  )
}


export default InfoPanel